"""ANFIS — système d'inférence neuro-flou adaptatif (Takagi-Sugeno, PyTorch).

Implémentation différentiable du réseau ANFIS de Jang (1993), à 5 couches :

1. **Fuzzification** : MF gaussiennes apprenables ``µ_{i,j}(x) = exp(-½((x−c)/σ)²)``.
2. **Règles** : force d'activation = produit des degrés (grille complète des MF).
3. **Normalisation** : ``w̄_r = w_r / Σ w``.
4. **Conséquents** : linéaires (TSK ordre 1) ``f_r = p_r·x + q_r`` (apprenables).
5. **Sortie** : ``Σ w̄_r · f_r``.

Tout est appris par rétropropagation (Adam), MF **et** conséquents conjointement.
À la différence du moteur Mamdani (règles fixées à la main), l'ANFIS apprend la
fonction de scoring à partir d'exemples entrée→sortie.

Cadrage dans le projet : l'ANFIS apprend l'agrégation **axes → score global**
(5 entrées = scores d'axes), en concurrence directe avec la couche d'inférence
Mamdani inter-axes. Cf. ``docs/methodology/03-anfis.md`` et le protocole de
validation à trois scorings (classique / flou / neuro-flou).

Nécessite l'extra ``fuzzy`` (torch).
"""

from __future__ import annotations

import itertools
from dataclasses import dataclass

import numpy as np
import torch
from torch import nn

_EPS = 1e-9


@dataclass
class ANFISConfig:
    n_inputs: int
    n_mfs_per_input: int = 2  # 2 MF/entrée -> 2^n_inputs règles (32 pour 5 axes)
    learning_rate: float = 0.02
    epochs: int = 400
    input_scale: float = 4.0  # entrées/sorties dans [0, input_scale]
    seed: int = 42

    @property
    def n_rules(self) -> int:
        return self.n_mfs_per_input**self.n_inputs


class _ANFISNet(nn.Module):
    """Réseau ANFIS différentiable (espace normalisé [0,1])."""

    def __init__(self, config: ANFISConfig) -> None:
        super().__init__()
        self.config = config
        n_in, n_mf = config.n_inputs, config.n_mfs_per_input

        # Centres initiaux répartis sur [0,1] ; largeurs raisonnables.
        centers0 = torch.linspace(0.0, 1.0, n_mf).repeat(n_in, 1)
        self.centers = nn.Parameter(centers0.clone())
        self.log_sigma = nn.Parameter(torch.full((n_in, n_mf), float(np.log(1.0 / n_mf))))

        # Grille complète des règles : (n_rules, n_inputs) d'indices de MF.
        combos = list(itertools.product(range(n_mf), repeat=n_in))
        self.register_buffer("rule_index", torch.tensor(combos, dtype=torch.long))

        # Conséquents linéaires TSK ordre 1.
        self.p = nn.Parameter(torch.zeros(config.n_rules, n_in))
        self.q = nn.Parameter(torch.zeros(config.n_rules))

    def forward(self, x: torch.Tensor) -> torch.Tensor:  # x: (batch, n_inputs) dans [0,1]
        sigma = torch.exp(self.log_sigma) + _EPS  # (n_in, n_mf)
        # Degrés d'appartenance gaussiens : (batch, n_in, n_mf)
        diff = x.unsqueeze(-1) - self.centers.unsqueeze(0)
        mu = torch.exp(-0.5 * (diff / sigma.unsqueeze(0)) ** 2)

        # Forces d'activation par règle (produit sur les entrées) : (batch, n_rules)
        firing = torch.ones(x.shape[0], self.config.n_rules, device=x.device)
        for i in range(self.config.n_inputs):
            idx_i = self.rule_index[:, i]            # (n_rules,)
            firing = firing * mu[:, i, :][:, idx_i]  # (batch, n_rules)

        w_bar = firing / (firing.sum(dim=1, keepdim=True) + _EPS)

        # Conséquents : (batch, n_rules)
        f = x @ self.p.t() + self.q
        return (w_bar * f).sum(dim=1)  # (batch,)


class ANFIS:
    """Interface haut niveau (façon scikit-learn) autour du réseau ANFIS."""

    def __init__(self, config: ANFISConfig) -> None:
        self.config = config
        torch.manual_seed(config.seed)
        self._net = _ANFISNet(config)
        self._fitted = False
        self.history_: list[float] = []

    def _to_unit(self, a: np.ndarray) -> torch.Tensor:
        return torch.tensor(a / self.config.input_scale, dtype=torch.float32)

    def fit(self, X: np.ndarray, y: np.ndarray, *, verbose: bool = False) -> ANFIS:
        """Entraîne MF et conséquents par descente de gradient (Adam, MSE)."""
        X = np.asarray(X, dtype=float)
        y = np.asarray(y, dtype=float)
        xt = self._to_unit(X)
        yt = torch.tensor(y / self.config.input_scale, dtype=torch.float32)

        opt = torch.optim.Adam(self._net.parameters(), lr=self.config.learning_rate)
        loss_fn = nn.MSELoss()
        self.history_ = []
        for epoch in range(self.config.epochs):
            opt.zero_grad()
            pred = self._net(xt)
            loss = loss_fn(pred, yt)
            loss.backward()
            opt.step()
            self.history_.append(float(loss.item()))
            if verbose and epoch % 50 == 0:
                print(f"epoch {epoch:4d}  loss={loss.item():.5f}")
        self._fitted = True
        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        """Prédit le score (dans [0, input_scale]) pour des entrées brutes."""
        if not self._fitted:
            raise RuntimeError("ANFIS non entraîné : appeler fit() d'abord.")
        with torch.no_grad():
            pred = self._net(self._to_unit(np.asarray(X, dtype=float)))
        out = pred.numpy() * self.config.input_scale
        return np.clip(out, 0.0, self.config.input_scale)

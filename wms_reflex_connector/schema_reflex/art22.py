# Copyright 2023 Akretion
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from dataclasses import dataclass

from .base import ReflexLine, ReflexLineDataBase


@dataclass(kw_only=True)
class ReflexLine22110Data(ReflexLineDataBase):
    code_interface: str = "22"
    code_rubrique: str = "110"
    code_article: str
    code_log_var: str
    code_type_id_log_var: str
    code_id_log_var: str


class ReflexLine22110(ReflexLine):
    def __init__(self, data: ReflexLine22110Data):
        super().__init__()
        self.data = data

    def get_values(self):
        data = self.data
        return [
            ("N° de séquence", 7, data.num_sequence),
            ("Code application", 2, data.code_application),
            ("Code interface", 2, "22", data.code_interface),
            ("Rubrique", 3, "110", data.code_rubrique),
            ("Code activité", 3, data.code_activity),
            ("Code article", 16, data.code_article),
            ("Code variante logistique", 2, data.code_log_var),
            (
                "Code type d'identifiant variante logistique",
                6,
                data.code_type_id_log_var,
            ),
            ("Code identifiant variante logistique", 35, data.code_id_log_var),
        ]

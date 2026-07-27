import unittest

from app import decodificar_atalho


class DecodificarAtalhoTests(unittest.TestCase):
    def test_normaliza_modificadores_e_letras(self):
        self.assertEqual(
            decodificar_atalho("alt+control+m"),
            ("Ctrl+Alt+M", 0x0003, ord("M")),
        )

    def test_aceita_tecla_de_funcao_sem_modificador(self):
        self.assertEqual(
            decodificar_atalho("f8"),
            ("F8", 0, 0x77),
        )

    def test_rejeita_letra_sem_modificador(self):
        with self.assertRaisesRegex(ValueError, "Ctrl, Alt, Shift ou Win"):
            decodificar_atalho("M")

    def test_rejeita_duas_teclas_principais(self):
        with self.assertRaisesRegex(ValueError, "apenas uma tecla"):
            decodificar_atalho("Ctrl+M+N")


if __name__ == "__main__":
    unittest.main()

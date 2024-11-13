# import unittest
# from unittest.mock import patch, MagicMock
# from app.engine.all_engine_strategies import all_engine_strategies


# class TestAllEngineStrategies(unittest.TestCase):
#     @patch("app.engine.all_engine_strategies.os.listdir")
#     @patch("app.engine.all_engine_strategies.importlib.import_module")
#     @patch("app.engine.all_engine_strategies.check_class_methods_and_variables")
#     def test_all_engine_strategies(
#         self, mock_check_class, mock_import_module, mock_listdir
#     ):
#         # Configurar los archivos en el directorio
#         mock_listdir.return_value = [
#             "strategy_one.py",
#             "strategy_two.py",
#             "__init__.py",
#             "base_strategy.py",
#         ]

#         # Mockear el módulo y la clase de cada estrategia
#         mock_module_one = MagicMock()
#         mock_module_two = MagicMock()
#         mock_strategy_class_one = MagicMock()
#         mock_strategy_class_two = MagicMock()

#         # Definir las clases en los módulos
#         mock_strategy_class_one.__name__ = "StrategyOne"
#         mock_strategy_class_two.__name__ = "StrategyTwo"
#         mock_module_one.StrategyOne = mock_strategy_class_one
#         mock_module_two.StrategyTwo = mock_strategy_class_two

#         # Mockear la importación de módulos
#         mock_import_module.side_effect = lambda name: {
#             "app.engine.strategy_one": mock_module_one,
#             "app.engine.strategy_two": mock_module_two,
#         }[name]

#         # Definir que ambas clases pasan el check de validación
#         mock_check_class.return_value = True

#         # Crear instancias de las clases y simular el método get_strategy_id()
#         mock_instance_one = MagicMock()
#         mock_instance_one.get_strategy_id.return_value = "strategy_one"
#         mock_strategy_class_one.return_value = mock_instance_one

#         mock_instance_two = MagicMock()
#         mock_instance_two.get_strategy_id.return_value = "strategy_two"
#         mock_strategy_class_two.return_value = mock_instance_two

#         # Ejecutar la función
#         result = all_engine_strategies()

#         # Verificar que las clases se hayan instanciado y validado correctamente
#         self.assertEqual(len(result), 2)
#         self.assertEqual(result[0].id, "strategy_one")
#         self.assertEqual(result[1].id, "strategy_two")
#         self.assertEqual(result[0].get_strategy_id(), "strategy_one")
#         self.assertEqual(result[1].get_strategy_id(), "strategy_two")

#         # Asegurar que la función check_class_methods_and_variables fue llamada para cada clase
#         mock_check_class.assert_any_call(mock_strategy_class_one)
#         mock_check_class.assert_any_call(mock_strategy_class_two)

#         # Asegurar que no se incluyó "BaseStrategy" o "__init__.py"
#         mock_listdir.assert_called_once_with("app/engine")


# if __name__ == "__main__":
#     unittest.main()

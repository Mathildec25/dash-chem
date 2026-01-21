# test_categorical.py
from bofire.data_models.features.api import CategoricalDescriptorInput
import pydantic
import bofire

print(f"Pydantic: {pydantic.__version__}")
print(f"BoFire: {bofire.__version__}")

# TEST 1: Exactement comme dans ton notebook
print("\n🧪 TEST 1: Copie exacte du notebook")
solvents = ["Methanol", "DMSO"]
descriptors = ["Boiling point"]
descriptor_values = [[64.7], [189.0]]

try:
    test_feature = CategoricalDescriptorInput(
        key="Solvent",
        categories=solvents,
        allowed=[True, True],
        descriptors=descriptors,
        values=descriptor_values
    )
    print("✅ TEST 1 PASSED!")
    print(f"   Feature créé: {test_feature.key}")
    print(f"   Categories: {test_feature.categories}")
except Exception as e:
    print(f"❌ TEST 1 FAILED: {e}")
    import traceback
    traceback.print_exc()

# TEST 2: Avec tes variables exactes de l'app
print("\n🧪 TEST 2: Avec name variable")
name = "Solvent"  # Exactement comme dans ton app

try:
    test_feature2 = CategoricalDescriptorInput(
        key=name,
        categories=solvents,
        allowed=[True] * len(solvents),
        descriptors=descriptors,
        values=descriptor_values
    )
    print("✅ TEST 2 PASSED!")
except Exception as e:
    print(f"❌ TEST 2 FAILED: {e}")
    import traceback
    traceback.print_exc()
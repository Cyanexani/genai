from llm_client import LLMClient


# Fake provider for testing
class FakeProvider:

    def generate(self, prompt):
        return "AI stands for Artificial Intelligence."


# Test LLM Client
def test_generate():

    provider = FakeProvider()

    client = LLMClient(provider)

    result = client.generate("Explain AI")

    assert result == "AI stands for Artificial Intelligence."
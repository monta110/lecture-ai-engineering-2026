"""第1回の質問スクリプトのテスト（LLM・APIキーは使わない）。"""

from types import SimpleNamespace

from app import ask


def test_interactive_reuses_chat_for_follow_up_questions(monkeypatch, capsys):
    sent_messages = []
    created_models = []

    class FakeChat:
        def send_message(self, message):
            sent_messages.append(message)
            return SimpleNamespace(text=f"回答: {message}", usage_metadata=None)

    class FakeClient:
        def __init__(self, api_key):
            assert api_key == "test-key"
            self.chats = SimpleNamespace(
                create=lambda model: create_chat(model)
            )

    def create_chat(model):
        created_models.append(model)
        return FakeChat()

    monkeypatch.setattr(ask.genai, "Client", FakeClient)
    monkeypatch.setattr(ask, "get_api_key", lambda: "test-key")
    questions = iter(["最初の質問", "続けて質問", "/exit"])

    def fake_input(prompt):
        assert prompt == "質問> "
        return next(questions)

    monkeypatch.setattr("builtins.input", fake_input)

    ask.ask_interactive()

    output = capsys.readouterr().out
    assert created_models == [ask.MODEL]
    assert sent_messages == ["最初の質問", "続けて質問"]
    assert output.count("[トークン数] 利用情報を取得できませんでした") == 2
    assert "回答: 最初の質問" in output
    assert "回答: 続けて質問" in output


def test_interactive_sends_initial_question_before_prompting(monkeypatch):
    sent_messages = []
    created_models = []

    class FakeChat:
        def send_message(self, message):
            sent_messages.append(message)
            return SimpleNamespace(text="回答", usage_metadata=None)

    class FakeClient:
        def __init__(self, api_key):
            assert api_key == "test-key"

            def create_chat(model):
                created_models.append(model)
                return FakeChat()

            self.chats = SimpleNamespace(create=create_chat)

    monkeypatch.setattr(ask.genai, "Client", FakeClient)
    monkeypatch.setattr(ask, "get_api_key", lambda: "test-key")

    def fake_input(prompt):
        assert prompt == "質問> "
        return "/exit"

    monkeypatch.setattr("builtins.input", fake_input)

    ask.ask_interactive("最初の質問")

    assert sent_messages == ["最初の質問"]
    assert created_models == [ask.MODEL]

"""第1回: 素のLLMに質問するスクリプト。

使い方:
    uv run python -m app.ask "LoRAとは何ですか？"
    uv run python -m app.ask            # 質問を省略すると、講座に固有の質問をする
    uv run python -m app.ask --interactive  # 会話履歴を保って続けて質問する

ツールを使わない「素の」呼び出し。
通常モードでは1回だけ質問し、会話モードでは実行中の履歴を保つ。
講座に固有のことを聞くと、「分からない」と答えるか、一般論でもっともらしく答える
（講座の実際とは違う）ことを確かめよう。
（第3回で、用語集を検索できるエージェントにして改善する）
"""

import argparse

from google import genai
from google.genai import errors

from app.config import MODEL, api_error_message, get_api_key

# 講座に固有の質問。正しい答えは data/glossary.json の homework-levels にある
DEFAULT_QUESTION = "AIE2026の講座の宿題にある「3レベル」とは何ですか？"


def print_usage(response) -> None:
    usage = response.usage_metadata
    if usage is None:
        print("[トークン数] 利用情報を取得できませんでした")
    else:
        input_tokens = usage.prompt_token_count
        output_tokens = usage.candidates_token_count
        input_display = input_tokens if input_tokens is not None else "不明"
        output_display = output_tokens if output_tokens is not None else "不明"
        print(f"[トークン数] 入力: {input_display} / 出力: {output_display}")


def ask(question: str) -> str:
    client = genai.Client(api_key=get_api_key())
    response = client.models.generate_content(model=MODEL, contents=question)
    print_usage(response)
    return response.text


def ask_interactive(first_question: str | None = None) -> None:
    client = genai.Client(api_key=get_api_key())
    chat = client.chats.create(model=MODEL)
    question = first_question

    while True:
        if question is None:
            try:
                question = input("質問> ").strip()
            except EOFError:
                print()
                return
        else:
            question = question.strip()

        if question.lower() in {"/exit", "exit", "quit", "終了"}:
            return
        if not question:
            question = None
            continue

        response = chat.send_message(question)
        print_usage(response)
        print(response.text)
        question = None


def main() -> None:
    parser = argparse.ArgumentParser(description="素のLLMに質問する")
    parser.add_argument("question", nargs="?")
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="会話履歴を保って続けて質問する（終了: /exit または Ctrl-D）",
    )
    args = parser.parse_args()

    print(f"[model] {MODEL}")
    try:
        if args.interactive:
            if args.question:
                print(f"[質問] {args.question}\n")
            ask_interactive(args.question)
        else:
            question = args.question or DEFAULT_QUESTION
            print(f"[質問] {question}\n")
            print(ask(question))
    except errors.APIError as e:
        print(api_error_message(e.code, e.message))
        raise SystemExit(1)


if __name__ == "__main__":
    main()

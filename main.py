"""revive - 支持多种大模型的智能聊天助手。"""

from config import get_default_config
from chat import create_client, list_providers


def main():
    default_cfg = get_default_config()
    provider = default_cfg.get("provider", "deepseek")
    model = default_cfg.get("model", "deepseek-chat")
    system_prompt = default_cfg.get("system_prompt", "你是一个有用的 AI 助手。")

    try:
        client = create_client()
    except ValueError as e:
        print(f"配置错误: {e}")
        print(f"可用提供商: {', '.join(list_providers())}")
        return
    except Exception as e:
        print(f"初始化失败: {e}")
        return

    print(f"revive 聊天助手已启动 (provider: {provider}, model: {model})")
    print("输入消息开始对话，输入 /reset 清空历史，输入 /exit 退出\n")

    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n再见！")
            break

        if not user_input:
            continue

        if user_input == "/exit":
            print("再见！")
            break

        if user_input == "/reset":
            client.reset()
            print("对话历史已清空。")
            continue

        try:
            reply = client.chat(user_input, system=system_prompt)
            print(f"AI: {reply}\n")
        except Exception as e:
            print(f"请求失败: {e}\n")


if __name__ == "__main__":
    main()

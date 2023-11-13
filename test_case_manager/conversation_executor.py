class ConversationExecutor:
    def __init__(self):
        pass

    def simulate_conversation(self, conversation_text):
        conversation_steps = conversation_text.strip().split("\n==CONVERSATION END==\n")
        bot_responses = []

        for step in conversation_steps:
            user_input = ""
            lines = step.split("\n")
            for line in lines:
                if line.startswith("[User]"):
                    user_input = line.replace("[User]", "").strip()
                    break
            bot_response = self.generate_bot_response(user_input)
            bot_responses.append(bot_response)

        return "\n".join(bot_responses)

    def generate_bot_response(self, user_input):
        return f"[Bot] This is a response to '{user_input}'"


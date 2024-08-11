from langchain_core.messages import AnyMessage
def get_message_content_str(message: AnyMessage) -> str:
    if type(message.content) == str:
        return message.content
    # check type list for content
    elif type(message.content) == list:
        for item in message.content:
            if isinstance(item, dict) and 'text' in item:
                return item['text']
    return str(message.content)
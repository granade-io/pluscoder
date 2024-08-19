from langchain_core.messages import AnyMessage
def get_message_content_str(message: AnyMessage) -> str:
    if type(message.content) is str:
        return message.content
    # check type list for content
    elif type(message.content) is list:
        for item in message.content:
            if isinstance(item, dict) and 'text' in item:
                return item['text']
    return str(message.content)
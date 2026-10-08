#заглушка
def generate_answer(
    question: str,
    context: list[dict]
) -> str:

    if not context:
        return "В базе знаний не найдено подходящей информации."

    context_text = "\n\n".join(
        item["text"]
        for item in context
    )

    return (
        "Я нашёл следующую информацию "
        "в базе знаний:\n\n"
        f"{context_text}"
    )
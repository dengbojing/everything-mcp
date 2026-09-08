"""Filename pinyin matching independent of MCP and ES."""


def pinyin_match(name: str, needle: str, mode: str, heteronym: bool) -> bool:
    """Bounded dynamic matching; no exponential polyphonic combinations."""
    from pypinyin import Style, pinyin

    readings = (
        [pinyin(char, style=Style.NORMAL, heteronym=True)[0] for char in name]
        if heteronym
        else pinyin(name, style=Style.NORMAL, errors=lambda chars: list(chars))
    )
    states = {0}
    for char, sounds in zip(name, readings):
        choices = set()
        if mode in ("full", "both", "mixed"):
            choices.update(sounds)
        if mode in ("initials", "both", "mixed"):
            choices.update(s[0] for s in sounds if s)
        if mode == "mixed":
            choices.add(char)
        next_states = {0}
        for index in states:
            for choice in choices:
                if needle.startswith(choice.lower(), index):
                    end = index + len(choice)
                    if end == len(needle):
                        return True
                    next_states.add(end)
        states = next_states
    return False

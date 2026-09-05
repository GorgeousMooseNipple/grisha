def mb_pretty(mb: float) -> str:
    units = ("Kb", "Mb", "Gb")
    value = mb * 1024.0

    for unit in units:
        pretty = f"{value:.2f} {unit}"
        if abs(value) < 1024:
            break
        value /= 1024.0
    return pretty

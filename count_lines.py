import requests
from tabulate import tabulate as tab

a = requests.get(
    "https://api.codetabs.com/v1/loc?github=Chaitanya-Keyal/Arcade&ignored=.github,LICENSE,.gitignore"
).json()
print(
    tab(
        a,
        dict(zip(a[0].keys(), [i[0].upper() + i[1:] for i in a[0].keys()])),
        "fancy_grid",
        stralign="center",
        numalign="right",
        showindex=list(range(1, len(a))) + [None],
    )
)

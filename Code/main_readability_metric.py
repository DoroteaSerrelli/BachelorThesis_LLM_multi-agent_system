# Esempio di funzione con complessità cognitiva da analizzare
from metrics import get_cognitive_complexity
from tabulate import tabulate


# Funzione di esempio
def f(n):
    if n > 10:
        return True
    if n < 5:
        return 20
    else:
        return 2
    return f(n)

total, details = get_cognitive_complexity(f)
print(tabulate(details, headers=["Complexity", "Node"], tablefmt="fancy_grid"))


# Calcolo della complessità cognitiva
if __name__ == "__main__":
    complexity, details = get_cognitive_complexity(f)
    print(f"Complessità cognitiva: {complexity}")

    # Stampa in formato tabellare
    print("\nDettagli della complessità:")
    print(tabulate(details, headers=["Complexity", "Code"], tablefmt="grid"))
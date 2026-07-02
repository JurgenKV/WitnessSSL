from typing import List


def get_domains(args):
    if args.file:
        domains = read_domains_from_file(args.file)
    elif args.domains:
        domains = args.domains
    else:
        # Если не указаны ни домены, ни файл – используем заглушку (для демонстрации)
        domains = read_domains_from_file("template.txt")

    return domains

def read_domains_from_file(filename: str) -> List[str]:
    """
    Читает домены из файла (по одному на строку).
    """
    # В оригинале заглушка для демонстрации. Раскомментируйте для реального использования.
    # with open(filename, 'r') as f:
    #     return [line.strip() for line in f if line.strip()]
    domains = ["Example.com"]
    return domains

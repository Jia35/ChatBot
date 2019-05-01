

with open("KnowledgeBase.json", "r") as f:
    txt = f.read()

txt = txt.split("\n\n")
b = []
for a in txt:
    a = a.replace(':', '],', 1)
    print(a)
    a = a.replace('  "', '{\n  "problem": ["', 1)
    print(a)
    a = a.replace('\n  [', '\n  "reply": [', 1)
    print(a)
    a = a.replace('\n  ],', '\n  ]\n},\n', 1)
    print(a)
    b.append(a)

# print(b)


with open("KnowledgeBase1.json", "w") as f:
    for line in b:
        f.write(line)

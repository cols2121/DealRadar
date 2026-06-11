import re, pathlib, glob

def fix_ac(text):
    lines = text.split('\n')
    in_ac = False
    result = []
    for line in lines:
        stripped = line.strip()
        if stripped == 'acceptance_criteria:':
            in_ac = True
            result.append(line)
            continue
        if in_ac:
            lm = re.match(r'^(\s*- )(.+)$', line)
            if lm:
                prefix, content = lm.group(1), lm.group(2)
                if (content.startswith('"') and content.endswith('"')) or \
                   (content.startswith("'") and content.endswith("'")):
                    result.append(line)
                else:
                    safe = content.replace('"', "'")
                    result.append(f'{prefix}"{safe}"')
                continue
            else:
                in_ac = False
        result.append(line)
    return '\n'.join(result)

files = glob.glob('spoq/epics/active/**/*.yml', recursive=True)
changed = 0
for f in files:
    path = pathlib.Path(f)
    text = path.read_text(encoding='utf-8')
    fixed = fix_ac(text)
    if fixed != text:
        path.write_text(fixed, encoding='utf-8')
        changed += 1
        print(f'Fixed: {f}')
print(f'Done. {changed}/{len(files)} files updated.')

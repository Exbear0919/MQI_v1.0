import json

data = json.load(open('C:/Users/Bear/WorkBuddy/20260402212518/indicators_v3.json','r',encoding='utf-8'))

# 查看无定义无公式的
no_content = [d for d in data if not d['definition'] and not d['formula']]
print('无定义无公式数量:', len(no_content))
print('\n前30个:')
for d in no_content[:30]:
    cat = d['category'][:20]
    name = d['name'][:60]
    print(f'  [{cat}] {name}')

# 查看名字包含垃圾的
print('\n名称含异常字符的:')
for d in data:
    if any(x in d['name'] for x in ['续表', '附件', 'MEDICAL', '页']):
        print(' ', d['name'][:80])

# 查看几个典型的神经系统指标
print('\n神经系统前5个:')
ns = [d for d in data if '神经系统' in d['category']]
for d in ns[:5]:
    print(f'  名称: {d["name"]}')
    print(f'  定义: {d["definition"][:80]}')
    print()

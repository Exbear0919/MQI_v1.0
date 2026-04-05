import json
data = json.load(open('indicators_clean.json','r',encoding='utf-8'))
has_formula = [d for d in data if d.get('formula')]
print('有公式指标总数:', len(has_formula))
for d in has_formula[:20]:
    print(f"  [{d['name'][:25]}] => {repr(d['formula'][:150])}")
print()
# 看子指标公式
for d in data:
    if d.get('sub_indicators'):
        for sub in d['sub_indicators']:
            if sub.get('formula'):
                print(f"  子[{sub['name'][:25]}] => {repr(sub['formula'][:150])}")

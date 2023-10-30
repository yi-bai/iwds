import datetime, os, json, requests
from bs4 import BeautifulSoup as bs
from PIL import Image

comp = json.loads(open('comp.json').read())
comp_map = {}
for row in comp:
    comp_map[row['code']] = row['zi']

comp_map['𠘺'] = '𠘺'
comp_map['䕫'] = '䕫'
comp_map['𦾱'] = '𦾱'
comp_map['徚'] = '徚'
comp_map['虩'] = '虩'
comp_map['祐'] = '祐'

head_ucv = f'''<?xml version="1.0" encoding="utf-8"?>
<html xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
 lang="ja">
<head>
  <title>Unifiable Component List</title>
  <link rel='stylesheet' type='text/css' href='pdf.css' />
  <link rel='stylesheet' type='text/css' href='iwds.css' />
  </head>
<body data-type="book">
  <div>
    <h1 style="text-align:center;">UCS Ideograph Unifiable Component Variations List</h1>
    <h2 style="text-align:center;" data-type="author">ISO/IEC JTC 1/SC 2/WG 2 IRG</h2>
    <h3 style="text-align:center;">Version: {datetime.date.today().strftime("%b/%d/%Y")}</h3>
  </div>
  <div data-type='toc'>
    <h2>Table of Contents</h2>
    <ol type='I'>
      <!--toc-->

'''

head_nucv = f'''<?xml version="1.0" encoding="utf-8"?>
<html xmlns='http://www.w3.org/1999/xhtml' lang='ja' xml:lang='ja'>
<head>
  <title>Not Unifiable Components</title>
  <base target='kanjidb' />
  <link rel='stylesheet' type='text/css' href='pdf.css' />
  <link rel='stylesheet' type='text/css' href='iwds.css'/>
</head>
<body data-type="book">
  <div>
    <h1 style="text-align:center;"> UCS Ideograph Non-Unifiable Component Variations List (NUCV) </h1>
    <h2 style="text-align:center;" data-type="author">ISO/IEC JTC 1/SC 2/WG 2 IRG</h2>
    <h3 style="text-align:center;">Version: {datetime.date.today().strftime("%b/%d/%Y")}</h3>
  </div>
  <div data-type='chapter' id='main'>
  <table style="width:100%;">
    <!--main-->
'''

head_ucv_summary = f'''<?xml version="1.0" encoding="utf-8"?>
<html xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
 lang="ja">
<head>
  <title>Unifiable Component Summary</title>
  <link rel='stylesheet' type='text/css' href='pdf.css' />
  <link rel='stylesheet' type='text/css' href='iwds-summary.css' />
  </head>
<body data-type="book">
  <div>
    <h1 style="text-align:center;">UCS Ideograph Unifiable Component Variations Summary List (UCV)</h1>
    <h2 style="text-align:center;" data-type="author">ISO/IEC JTC 1/SC 2/WG 2 IRG</h2>
    <h3 style="text-align:center;">Version: {datetime.date.today().strftime("%b/%d/%Y")}</h3>
  </div>
  <div data-type='toc'>
    <h2>Table of Contents</h2>
    <ol type='I'>
      <!--toc-->

'''
head_nucv_summary = f'''<?xml version="1.0" encoding="utf-8"?>
<html xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
 lang="ja">
<head>
  <title>Unifiable Component Summary</title>
  <link rel='stylesheet' type='text/css' href='pdf.css' />
  <link rel='stylesheet' type='text/css' href='iwds-summary.css' />
  </head>
<body data-type="book">
  <div>
    <h1 style="text-align:center;"> UCS Ideograph Non-Unifiable Component Variations Summary List (NUCV) </h1>
    <h2 style="text-align:center;" data-type="author">ISO/IEC JTC 1/SC 2/WG 2 IRG</h2>
    <h3 style="text-align:center;">Version: {datetime.date.today().strftime("%b/%d/%Y")}</h3>
  </div>
  <div data-type='chapter' id='main'>
    <!--main-->

'''

tail = '''  </table>
</div>
</body>
</html>
'''

def content_links(iwds):
    groups = iwds.find_all('group')
    ret = []
    for group in groups:
        ret.append(f"  <li><a href='#{group['id']}'>{group['en']}</a></li>")
        for subgroup in group.find_all('subgroup'):
            ret.append(f"  <li><a href='#{subgroup['id']}'>{subgroup['en']}</a></li>")
    ret[-1] = ret[-1]+'    </ol>'
    ret.append('''  </div>
  <div data-type='chapter' id='main'>
  <table>
  <!--main-->

''')
    return '\n'.join(ret)

def content_links_summary(iwds):
    groups = iwds.find_all('group')
    ret = []
    for group in groups:
        ret.append(f"  <li><a href='#{group['id']}'>{group['en']}</a></li>")
        for subgroup in group.find_all('subgroup'):
            ret.append(f"  <li><a href='#{subgroup['id']}'>{subgroup['en']}</a></li>")
    ret[-1] += '    </ol>'
    ret += ['''  </div>
  <div data-type='chapter' id='main'>
    <!--main-->

  </div>
''']
    return '\n'.join(ret)

def parse_group(group, nucv=False):
    head = f'''  <tr>
    <td colspan='3'>
      <div id='{group['id']}'><h3>{group['en']}</h3></div>
    </td>
  </tr>'''
    ret = [head] if not nucv else []
    for subgroup in group.find_all('subgroup') or [group]:
        ret += parse_subgroup(subgroup, contains_head=subgroup!=group, nucv=nucv)
    return '\n'.join(ret+[''])

def parse_group_summary(group, nucv=False):
    head = [f'''  <div id='{group['id']}'><h3>{group['en']}</h3></div>
  <div class='multicol'>
''']
    if not nucv and group.find_all('subgroup'):
        head += ['  </div>']
    ret = head if not nucv else []
    for subgroup in group.find_all('subgroup') or [group]:
        ret += parse_subgroup_summary(subgroup, contains_head=subgroup!=group, nucv=nucv)
    return '\n'.join(ret+[''])

def parse_subgroup(subgroup, contains_head=True, nucv=False):
    head = f'''  <tr>
    <td colspan='3'>
      <div id='{subgroup['id']}'><h3>{subgroup['en']}</h3></div>
    </td>
  </tr>'''
    ret = [head] if contains_head and not nucv else []
    for entry in subgroup.find_all('entry'):
        if not nucv and entry["kind"] != 'unifiable' or nucv and entry["kind"] == 'unifiable': continue
        ret += parse_entry(entry)
    return ret

def parse_subgroup_summary(subgroup, contains_head=True, nucv=False):
    head = f'''  <div id='{subgroup['id']}'><h3>{subgroup['en']}</h3></div>
  <div class='multicol'>
'''
    ret = [head] if contains_head and not nucv else []
    for entry in subgroup.find_all('entry'):
        if not nucv and entry["kind"] != 'unifiable' or nucv and entry["kind"] == 'unifiable': continue
        ret += parse_entry_summary(entry)

    if not nucv: ret += ['  </div>']
    return ret

def download_glyph(glyph):
    png = requests.get(f'https://glyphwiki.org/glyph/{glyph}.png')
    if not png.status_code==200:
        exit(f'failed to download image {glyph}')
    open(f'./glyphs/{glyph}.png','wb').write(png.content)
    svg = requests.get(f'https://glyphwiki.org/glyph/{glyph}.svg')
    if not svg.status_code==200:
        exit(f'failed to download image {glyph}')
    open(f'./glyphs/{glyph}.svg','wb').write(svg.content)
    print(f'downloaded glyph {glyph}')

def parse_entry(entry):
    #print(entry['id'])
    head = f"  <tr id='{entry['id']}'>"
    col1 = f"    <td>{entry['id']}</td>"
    col2 = ["    <td>"] + [f"<div style='position:absolute; z-index:-1'>{entry.find('components').text}</div>"] + [f"      <img height='26' width='26' src='./glyphs/{glyph}.png'/>" for glyph in entry.find('glyphs').text.split(',')] + ["    </td>"]
    for glyph in entry.find('glyphs').text.split(','):
        path = f'./glyphs/{glyph}.png'
        if not os.path.exists(path): download_glyph(glyph)

    col3 = ["    <td>"]
    if entry.get('level'):
        col3 += [f"Level: {entry.get('level')}<br/>"]
    if entry.find('jis'):
        for jis in entry.find('jis').text.split(','):
            col3 += [f"      <img src='fig/jis.{jis}.gif' alt='jis.{jis}'/> (JIS X 0213 - {jis})<br/>"]
    if entry.find('hydcd'):
        col3 += [f"      <img src='fig/xinjiu{entry.find('hydcd').text}.png' alt='hydcd.{entry.find('hydcd').text}'/> (HYDCD - {entry.find('hydcd').text})<br/>"]
    for k in ['sourcecodeseparation','disunified','compatibles','unified']:
        x = entry.find(k)
        if not x: continue
        if not x.text: continue
        col3 += parse_col3(k, x.text)
    if entry.find('note'):
        col3 += [f'''      <hr width='90%' size=4/>
      <h4>Note</h4>{entry.find('note').text}''']
    if entry.find('reviewsystem'):
        for reviewsystem in entry.find_all('reviewsystem'):
            col3 += [f'''      <hr width='90%' size=4/>
      <h4>Review System</h4>
      <a href='{reviewsystem.text}'>{reviewsystem.text}</a>''']

    tail = '''    </td>
  </tr>'''

    return [head]+[col1]+col2+col3+[tail]

def parse_entry_summary(entry):
    #print(entry['id'])  <table><tr id='1'>

    head = f'''  <table style="-webkit-column-break-inside:avoid;"><tr id='{entry['id']}'>
    <td>{entry['id']}{'*' if entry.get('level')=='2' else ''}</td>'''
    col2 = ["    <td>"] + [f"      <img height='26' width='26' src='./glyphs/{glyph}.png'/>" for glyph in entry.find('glyphs').text.split(',')] + ["    </td>"]
    col3 = [f'''    <td style="font-family:initial;"><div style="min-height:32px;">{entry.find('unified').text.replace('*','').replace('$','').replace('#','') if entry.find('unified') else ''}
    </div></td>''']

    tail = '''  </tr></table>'''

    return [head]+col2+col3+[tail]
    
def tokenize(t):
    if t[-1] == '…': t = t[:-1]
    cur = 0
    ret = []
    while True:
        if not cur<len(t): break
        ret.append(t[cur])
        cur += 1
        if not cur<len(t): break
        if t[cur] in '*#$':
            ret[-1] = ret[-1] + t[cur]
            cur += 1
    return ret

def parse_col3(k, text):
    if k in set(['sourcecodeseparation','disunified']): entries = [tokenize(s) for s in text.split(',')]
    else: entries = [[s] for s in tokenize(text)]

    if k=='compatibles': entries = [[comp_map[x[0][0]]+(x[0][1] if len(x[0])>1 else '')]+x for x in entries]
    
    head = {'sourcecodeseparation':'Source Code Separations','disunified':'Disunified Ideographs','compatibles':'Compatibility Ideographs','unified':'Unified Ideographs'}[k]
    if text[-1]=='…': head += ' (Examples)'
    head = f"      <h3>{head}</h3>"
    ret = (["      <hr widh='90%' size='4'/>"] if k in set(['sourcecodeseparation','disunified']) else ["      <hr widh='90%' size=4/>"]) + [head] + ['      <table>']
    for entry in entries:
        ret += parse_col3_row(entry)
    ret += ['      </table>']
    return ret

def parse_col3_row(entries):
    return ['        <tr>'] + [parse_col3_col(e) for e in entries] + ['        </tr>']

def parse_col3_col(entry):
    h = lambda x: hex(ord(x))[2:].upper().zfill(5)
    def height(x,im,supercjk):
        if supercjk: return 62
        if im and im[1]==260: return 28
        if im and im[1]>=515: return 57
        if len(x)==1: return 29
        elif x[1]=='*': return 31
        elif x[1]=='$': return 30
        return 62
    def source(x):
        if len(x)==1: return 'ucs2017'
        elif x[1]=='*': return 'ucs2003'
        elif x[1]=='$': return 'ucs2014'
        return 'ucs2017'
    path = f'./{source(entry)}/{h(entry[0])}.png'
    im,supercjk = None,False
    try:
        if not os.path.exists(path): path,supercjk = f'./supercjk/{h(entry[0])}.png',True
        im = Image.open(path).size
    except:
        print(path, 'not exists!!!')
    return f'''          <td><div style='position:absolute; z-index:-1'>{entry[0]}{h(entry[0])}</div>
              <img height='{height(entry,im,supercjk)}' src='{path}' alt=''/></td>'''

iwds = bs(open('iwds.xml').read())

print('generating ucv.html...')
o = open('ucv.html','w')
o.write(head_ucv)
o.write(content_links(iwds))
for group in iwds.find_all('group'):
    o.write(parse_group(group))
o.write(tail)

print('generating nucv.html...')
o = open('nucv.html','w')
o.write(head_nucv)
for group in iwds.find_all('group'):
    o.write(parse_group(group, nucv=True))
o.write(tail)

print('generating ucv-summary.html...')
o = open('ucv-summary.html','w')
o.write(head_ucv_summary)
o.write(content_links_summary(iwds))
for group in iwds.find_all('group'):
    o.write(parse_group_summary(group))
o.write(tail)

print('generating nucv-summary.html...')
o = open('nucv-summary.html','w')
o.write(head_nucv_summary)
for group in iwds.find_all('group'):
    o.write(parse_group_summary(group, nucv=True))
o.write(tail)
import os, json, re
from pathlib import Path
import streamlit as st

APP_DIR = Path(__file__).parent
PDF_PATH = APP_DIR / 'UPPG_Master_Plan_Guide.pdf'
TEXT_PATH = APP_DIR / 'guide_pages.txt'
STATE_PATH = APP_DIR / '.poc_state.json'

st.set_page_config(page_title='Master Plan AI Assistant', page_icon='🏙️', layout='wide')

# ---------- Demo knowledge extracted from the uploaded UPPG ----------
DEMO_KB = [
    {
        'title':'What is the Master Plan Permit?',
        'page':'18',
        'text':'A Master Plan Permit authorizes development works for subdivision of unzoned land and determination of its use, major modifications to an approved Master Plan, and updates resulting from cumulative parcel-level changes exceeding approved threshold limits. It is also used for new real estate master plan development and modifications to existing master plans.'
    },
    {
        'title':'General submission requirements',
        'page':'12',
        'text':'General submission requirements include: Master Plan Report; Master Plan in Geographic Information Systems format; Project development budget including zoning, population and infrastructure requirements in Microsoft Excel. Quantities shall use metric units with units defined. For calculated ratios/percentages, land areas and GFA are exact; population, public facilities and parking are rounded down.'
    },
    {
        'title':'Master Plan approval process',
        'page':'23',
        'text':'Core process: follow submission guideline; apply for initial MP application; initial completeness review; review of Alignment Report and Public Facilities Provision; obtain Structure Plan 2040 alignment information; alignment approval and initial MP review/approval; Statement of Submission preparation/submission; authority coordination where applicable; final SoS approvals; final MP preparation/submission; final MP approval. All submissions and correspondence are through the unified Urban Planning Portal.'
    },
    {
        'title':'Dubai 2040 alignment',
        'page':'14',
        'text':'Alignment with Dubai 2040 Plan and conformity with Public Facilities provision standards are a mandatory stage in the Master Plan approval process for new subdivision of unzoned land, major modifications exceeding 10% of an approved Master Plan, and modifications affecting previously approved Dubai 2040 parameters. Reviewing criteria include land use, target densities, public recreational open space (5% of total project area), optional affordable housing, TOD requirements, Urban Centers requirements, and public facilities.'
    },
    {
        'title':'Who can submit?',
        'page':'12',
        'text':'Applications use the Unified Urban Planning Portal. A Master Plan can be submitted by the owner/developer, an appointed consultant, or the Planning Authority in the circumstances described by the guideline.'
    },
    {
        'title':'Major modification studies',
        'page':'19-20',
        'text':'For major Master Plan modifications, the guideline provides thresholds and identifies required/optional studies. Examples include parcel configuration changes exceeding +10% or 10,000 sqm; GFA distribution changes; changes to total GFA; planning regulations/urban design changes; transportation changes; utilities changes; phasing changes; and population impacts exceeding +10% or 2,000 residents/workers/visitors. Depending on the modification, public facilities feedback, traffic impact, environmental impact, utilities impact and market studies may be required.'
    },
    {
        'title':'Making a good application',
        'page':'25-50',
        'text':'The guideline covers site analysis and SWOT, population served, development concept, land use plans, building heights and white block massing, residential/commercial/hospitality, public facilities, urban design and public realm, environment and sustainability, transport, utilities and other master plan components. Supporting documents or additional studies may be requested for specific aspects.'
    },
]

SYSTEM_PROMPT = '''You are the Master Plan AI Assistant POC for Dubai Urban Planning Permits.

Your ONLY authoritative source for planning requirements is the uploaded Urban Planning Permits Guideline (UPPG), especially the Master Plan Permit section and appendices. Do not invent requirements. If the guide does not support an answer, say so clearly and identify what additional official source would be needed.

Behavior:
1. Answer in the user's language (Arabic or English). Preserve official terms such as Master Plan Permit, Planning Permit, Unified Urban Planning Portal, Dubai 2040, Structure Plan, Public Facilities, GIS, GFA, etc.
2. Explain requirements in practical language, but distinguish the guide's requirement from your explanation.
3. Always provide a concise source reference at the end, using the page number(s) you can identify from the retrieved material. If page number is uncertain, say "Source: UPPG (relevant section)" rather than guessing.
4. Never claim that an AI answer is an approval, legal opinion, or final compliance determination. Use "preliminary guidance" or "preliminary completeness check" where appropriate.
5. When asked to generate a checklist, organize it as Required / Conditional or Context-dependent / Additional or may be requested.
6. When the user describes a project, ask only the minimum clarifying questions needed to determine which requirements apply.
7. For permit-type questions, distinguish Master Plan Permit (MPP), Planning Permit (PP), and General Planning Permit (GPP) using the UPPG criteria.
8. Be conservative: if two requirements could depend on project context, say that explicitly.
'''


def load_state():
    if STATE_PATH.exists():
        try: return json.loads(STATE_PATH.read_text(encoding='utf-8'))
        except Exception: pass
    return {}

def save_state(state):
    STATE_PATH.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding='utf-8')

def demo_answer(q):
    ql=q.lower()
    hits=[]
    terms={
        'master plan permit':['master plan permit','mpp','اعتماد المخطط العام','المخطط العام'],
        'general submission requirements':['requirements','documents','required','مستندات','متطلبات','المطلوب','checklist'],
        'master plan approval process':['process','steps','procedure','approval','إجراءات','خطوات','اعتماد'],
        'dubai 2040 alignment':['2040','alignment','دبي 2040','المواءمة'],
        'who can submit?':['who can submit','submit','تقديم','يقدم'],
        'major modification studies':['modification','change','study','studies','تعديل','دراسة','دراسات'],
    }
    for item in DEMO_KB:
        score=0
        for key, words in terms.items():
            if item['title']==key and any(w in ql for w in words): score += 3
        score += sum(1 for w in re.findall(r'[A-Za-z0-9]+', ql) if w.lower() in item['text'].lower())
        if score: hits.append((score,item))
    hits.sort(key=lambda x:x[0], reverse=True)
    if not hits:
        return 'في وضع الـ Demo المحلي، لم أجد إجابة موثوقة في قاعدة المعرفة المصغرة. شغّل وضع AI بعد إضافة OPENAI_API_KEY لاستخدام البحث في الدليل الكامل.\n\nSource: UPPG demo knowledge base.'
    best=[x[1] for x in hits[:2]]
    if 'checklist' in ql or 'documents' in ql or 'متطلبات' in ql or 'المطلوب' in ql:
        return ('### Preliminary Master Plan Submission Checklist\n\n'
                '- ☐ Master Plan Report\n- ☐ Master Plan in GIS format\n- ☐ Project development budget in Microsoft Excel, including zoning, population and infrastructure requirements\n- ☐ Confirm metric units and defined units\n- ☐ Confirm applicable Dubai 2040 alignment / Public Facilities requirements\n\n'
                '**Note:** Additional studies or supporting documents may be requested depending on the project and specific aspects.\n\n'
                '**Source:** UPPG pp. 12, 14, 24.')
    out=[]
    for x in best:
        out.append(f"**{x['title']}**\n{x['text']}\n\n_Source: UPPG p. {x['page']}_")
    return '\n\n---\n\n'.join(out)


def setup_vector_store(client):
    state=load_state()
    if state.get('vector_store_id'):
        return state['vector_store_id']
    if not PDF_PATH.exists():
        raise FileNotFoundError('UPPG_Master_Plan_Guide.pdf not found')
    vs=client.vector_stores.create(name='Dubai UPPG - Master Plan POC')
    with open(PDF_PATH,'rb') as f:
        uploaded=client.files.create(file=f, purpose='assistants')
    # Current OpenAI Python SDK supports create_and_poll for vector store files.
    client.vector_stores.files.create_and_poll(vector_store_id=vs.id, file_id=uploaded.id)
    state['vector_store_id']=vs.id
    state['source_file_id']=uploaded.id
    save_state(state)
    return vs.id


def ai_answer(client, vs_id, history, question):
    context='\n'.join([f"{m['role']}: {m['content']}" for m in history[-8:]])
    prompt=f'''Conversation so far:\n{context}\n\nUser's latest question:\n{question}\n\nUse file search against the UPPG before answering. Keep the answer practical and concise.'''
    response=client.responses.create(
        model=os.getenv('OPENAI_MODEL','gpt-5-mini'),
        instructions=SYSTEM_PROMPT,
        tools=[{'type':'file_search','vector_store_ids':[vs_id]}],
        input=prompt,
        store=False,
    )
    return response.output_text

# ---------- UI ----------
st.markdown('''<style>
.main-title{font-size:2.2rem;font-weight:800;margin-bottom:.2rem}.sub{color:#667085;margin-bottom:1.2rem}
.card{padding:18px;border:1px solid #e4e7ec;border-radius:14px;background:#fff;margin-bottom:12px}
.badge{display:inline-block;padding:4px 9px;border-radius:20px;background:#eef4ff;color:#344054;font-size:.82rem}
</style>''', unsafe_allow_html=True)

st.markdown('<div class="main-title">🏙️ Master Plan AI Assistant</div>', unsafe_allow_html=True)
st.markdown('<div class="sub">POC — Urban Planning Permits Guideline (UPPG) • Master Plan Permit</div>', unsafe_allow_html=True)

with st.sidebar:
    st.header('POC Controls')
    mode=st.radio('Mode', ['Demo (no API key)', 'AI + UPPG RAG'])
    st.caption('The AI mode searches the uploaded UPPG before answering.')
    if st.button('Reset conversation'):
        st.session_state.messages=[]
        st.rerun()
    st.divider()
    st.markdown('**Demo scenario**')
    st.write('1. Identify permit\n2. Explain requirements\n3. Generate checklist\n4. Explain process\n5. Show source')
    st.divider()
    st.caption('This is a demonstration/prototype. It is not an approval or legal/compliance determination.')

if 'messages' not in st.session_state:
    st.session_state.messages=[]

col1,col2,col3,col4=st.columns(4)
for col, title, q in [
    (col1,'📋 Requirements','What documents are required for a Master Plan Permit?'),
    (col2,'🔎 Process','Explain the Master Plan approval process step by step.'),
    (col3,'🧭 Permit type','When is a Master Plan Permit used?'),
    (col4,'📝 Checklist','Create a preliminary submission checklist for a new master plan.')]:
    if col.button(title, use_container_width=True):
        st.session_state.pending=q

for m in st.session_state.messages:
    with st.chat_message(m['role']):
        st.markdown(m['content'])

question=st.chat_input('Ask about Master Plan Permit requirements, process, checklist, Dubai 2040 alignment...')
if 'pending' in st.session_state and not question:
    question=st.session_state.pop('pending')

if question:
    st.session_state.messages.append({'role':'user','content':question})
    with st.chat_message('user'): st.markdown(question)
    with st.chat_message('assistant'):
        with st.spinner('Searching the UPPG…'):
            if mode.startswith('AI'):
                try:
                    from openai import OpenAI
                    if not os.getenv('OPENAI_API_KEY'):
                        raise RuntimeError('OPENAI_API_KEY is not set. Use Demo mode or add your key.')
                    client=OpenAI()
                    vs=setup_vector_store(client)
                    answer=ai_answer(client,vs,st.session_state.messages[:-1],question)
                except Exception as e:
                    answer=f"⚠️ AI mode is not ready: `{e}`\n\nSwitch to **Demo** mode for the presentation, or set `OPENAI_API_KEY` and run again."
            else:
                answer=demo_answer(question)
        st.markdown(answer)
    st.session_state.messages.append({'role':'assistant','content':answer})

st.divider()
st.caption('Source basis: 202608 UPP — Guidelines — Final Version 01.pdf (139 pages). The guide states that it unifies the urban planning permits submission approach and directs applicants to identify the correct permit and follow the submission checklist.')

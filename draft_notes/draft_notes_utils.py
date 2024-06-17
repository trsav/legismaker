import os 
from bs4 import BeautifulSoup
import requests
import ast
import anthropic
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import utils
import datetime
import PyPDF2
from docx import Document
import ast
from pprint import pprint
from newscatcherapi_client import Newscatcher, ApiException
import re
import json
import anthropic 
import os 
from bs4 import BeautifulSoup
import requests

def get_legislation(path):
    url = path
    response = requests.get(url)
    if response.ok:
        print("Ok!")
        print(response.url)
    soup = BeautifulSoup(response.text, 'xml')
    section_ids = [section.P1.get("id") for section in soup.find_all("P1group")]
    section_ids = [section for section in section_ids if section is not None]
    section_texts = [soup.find(id=section_ids[i]).get_text(" ") for i in range(len(section_ids))]
    return section_ids,section_texts


import json 
def parse_act(act_json_path):
    with open(act_json_path,'r') as f:
        act = json.load(f)
    # produce two list, one with section or subsection titles and the other with the text of the sections or subsections
    # traverse subsections
    titles = []
    texts = []
    name = []
    for section in act['sections']:
        # traverse all sub and subsubsections and get all text
        titles.append(section['title'])
        name.append(section["name"])
        section_text = []
        print(section)
        for subsection in section['content']:
            section_text.append(subsection['subsection'] + ' ' + subsection['text'])
            try:
                for subsubsection in subsection['content']:
                    section_text.append(subsubsection['subsubsection'] + ' ' +subsubsection['text'])
            except:
                pass
        section_text = '. '.join(section_text)
        texts.append(section_text)
    return titles, texts, name

def sort_sections(section):
    return int(re.search(r'\d+', section).group())

# titles,texts = parse_act('Documents/act.json')
# print(titles)

################################################
#### Explanatory note: Commentary functions ####
################################################

def get_image(path, width=1*inch):
    img = utils.ImageReader(path)
    iw, ih = img.getSize()
    aspect = ih / float(iw)
    return Image(path, width=width, height=(width * aspect))

def read_keys():
    '''
    reads API keys from .env file in root directory. 
    '''
    with open('.env') as f:
        for line in f:
            var = line.strip().split('=')
            if len(var) == 2:
                key, value = var
                os.environ[key] = value
# read_keys()

# creating client with api key from .env file
anthropic_client = anthropic.Anthropic(
    api_key=os.environ.get('ANTHROPIC_API_KEY'))

def get_commentary(legislation_section_title, legislation_section, section_number, model):

    system = f"""
Your task is to provide commentary to a piece of existing legislation as part of an explanatorty note. 

Explanatory Notes were introduced in 1999 to go with every Bill which passes through Parliament. The notes are designed to assist readers who do not have legal training and are unfamiliar with the subject matter of the bill.
Please note it should not explain the orginal legislation but reiterate it in simple everyday language, but still detailed.
You must return the line-by-line commentary for each section of the associated legislation.
This is key to the interpretation of the legislation for readers who do not have legal training and are unfamiliar with the subject matter of the bill.

Here is a framework you must follow: 
"Commentary on provisions of the bill” section 
This is also known as ‘line by line’ and provides a simple summary of a measure to allow a layperson to understand what it does.
Return your output as a python Dictionary.
The commentary must never simply restate what the bill says, but should stand back from the detail of the provision and try to summarise it in one or two sentences, using everyday language. The notes must be neutral in tone (ie they do not go into political lines about the merits of the policy, though the practical outcomes should be spelled out), written in plain language, with short sentences and paragraphs. It is important to avoid jargon and to explain the meaning of any technical or legal terms and any acronyms or other abbreviations.
The purpose of the commentary is also to add value – what will it be helpful for the reader to know that is not apparent from reading the bill itself? We want to see if the tool can write this using the following information: 
Information that it might be helpful to include is: 
●   factual background;
●   an explanation of how the provision interacts with other legislation (whether other provisions of the bill or of existing legislation);
●   definitions of technical terms used in the bill;
●   illustrative examples of how the bill will work in practice (these might perhaps be worked examples of a calculation or examples of how a new offence might be committed); 
●   an explanation of how the department plans to use the provision.

Here is an example of what you must provide. 

<example>
<legislation>
2 Fraud by false representation
(1) A person is in breach of this section if he—
(a) dishonestly makes a false representation, and
(b) intends, by making the representation—
(i) to make a gain for himself or another, or
(ii) to cause loss to another or to expose another to a risk of loss.
(2) A representation is false if—
(a) it is untrue or misleading, and
(b) the person making it knows that it is, or might be, untrue or misleading.
(3) “Representation” means any representation as to fact or law, including a representation
as to the state of mind of—
(a) the person making the representation, or
(b) any other person.
(4) A representation may be express or implied.
(5) For the purposes of this section a representation may be regarded as made if it (or
anything implying it) is submitted in any form to any system or device designed to
receive, convey or respond to communications (with or without human intervention).
</legislation>

<explanatory note>
Section 2 makes it an offence to commit fraud by false representation. 
Subsection (1)
makes clear that the representation must be made dishonestly. This test applies also
to sections 3 and 4. The current definition of dishonesty was established in R v Ghosh
[1982] Q.B.1053. That judgment sets a two-stage test. The first question is whether
a defendant’s behaviour would be regarded as dishonest by the ordinary standards of
reasonable and honest people. If answered positively, the second question is whether the
defendant was aware that his conduct was dishonest and would be regarded as dishonest
by reasonable and honest people.
Subsection (1)(b) requires that the person must make the representation with the
intention of making a gain or causing loss or risk of loss to another. The gain or loss does
not actually have to take place. The same requirement applies to conduct criminalised
by sections 3 and 4.
Subsection (2) defines the meaning of “false” in this context and subsection (3) defines
the meaning of “representation”. A representation is defined as false if it is untrue or
misleading and the person making it knows that it is, or might be, untrue or misleading.
Subsection (3) provides that a representation means any representation as to fact or law,
including a representation as to a person’s state of mind.
Subsection (4) provides that a representation may be express or implied. It can be stated
in words or communicated by conduct. There is no limitation on the way in which
the representation must be expressed. So it could be written or spoken or posted on a
website.
A representation may also be implied by conduct. An example of a representation
by conduct is where a person dishonestly misuses a credit card to pay for items. By
tendering the card, he is falsely representing that he has the authority to use it for that
transaction. It is immaterial whether the merchant accepting the card for payment is
deceived by the representation.
This offence would also be committed by someone who engages in “phishing”: i.e.
where a person disseminates an email to large groups of people falsely representing
that the email has been sent by a legitimate financial institution. The email prompts the
reader to provide information such as credit card and bank account numbers so that the
“phisher” can gain access to others’ assets.
Subsection (5) provides that a representation may be regarded as being made if it (or
anything implying it) is submitted in any form to any system or device designed to
receive, convey or respond to communications (with or without human intervention).
The main purpose of this provision is to ensure that fraud can be committed where a
person makes a representation to a machine and a response can be produced without
any need for human involvement. (An example is where a person enters a number into a
“CHIP and PIN” machine.) The Law Commission had concluded that, although it was
not clear whether a representation could be made to a machine, such a provision was
unnecessary (see paragraph 8.4 of their report). But subsection (5) is expressed in fairly
general terms because it would be artificial to distinguish situations involving modern
technology, where it is doubtful whether there has been a “representation”, because the
only recipient of the false statement is a machine or a piece of software, from other
situations not involving modern technology where a false statement is submitted to a
system for dealing with communications but is not in fact communicated to a human
being (e.g., postal or messenger systems).
</explanatory note>

Another example.

<legislation>
Section 5 “Gain” and “loss”
(1) The references to gain and loss in sections 2 to 4 are to be read in accordance with
this section.
(2) “Gain” and “loss”—
(a) extend only to gain or loss in money or other property;
(b) include any such gain or loss whether temporary or permanent;
and “property” means any property whether real or personal (including things in action
and other intangible property).
(3) “Gain” includes a gain by keeping what one has, as well as a gain by getting what
one does not have.
(4) “Loss” includes a loss by not getting what one might get, as well as a loss by parting
with what one has.
</legislation>

<exaplanatory note>
Section 5: “Gain” and “loss”
Section 5 defines the meaning of “gain” and “loss” for the purposes of sections 2 to
4 The definitions are essentially the same as those in section 34(2)(a) of the Theft
Act 1968 and section 32(2)(b) of the Theft Act (Northern Ireland) 1969. Under these
definitions, “gain” and “loss” are limited to gain and loss in money or other property.
The definition of “property” which applies in this context is based on section 4(1) of
the Theft Act 1968 (read with section 34(1) of that Act) and section 4(1) of the Theft
Act (Northern Ireland) 1969 (read with section 32(1) of that Act). The definition of
“property” covers all forms of property, including intellectual property, although in
practice intellectual property is rarely “gained” or “lost”.
</explanatory note>"""

    prompt = f"""
<legislation>
{legislation_section_title}
{section_number}
{legislation_section}
</legislation>"""
    response = f"""
<explanatory note>"""

    res = anthropic_client.messages.create(
        model=model,
        temperature=0.8,
        system=system,
        max_tokens = 4016,
        messages=[
            {"role": "user", "content": [{"type": "text", "text": prompt}]},
            {"role": "assistant", "content": [{"type": "text", "text": response}]},
        ],
    )

    res = res.content[0].text.split("</explanatory note>")[0]
    return res


def create_explanation_document(path,section_titles,explanations,title,policy_background):

    current_time_string = str(datetime.datetime.now(datetime.UTC))
    path += '.pdf'
    doc = SimpleDocTemplate(path, pagesize=letter)
    styles = getSampleStyleSheet()
    elements = []
    # add header with UTC and metadata at beginning
    creation_time = str(datetime.datetime.now(datetime.UTC))[:-13]
    header_style = ParagraphStyle(name='Header', fontSize=10, leading=12, alignment=1)
    elements.append(Paragraph(f"Modified - {creation_time}, NOT FINAL - CREATED USING GENERATIVE AI.", header_style))
    elements.append(Spacer(1, 0.25 * inch))
    title_style = ParagraphStyle(name='Title', fontSize=20, leading=24, spaceAfter=12, alignment=1)

    # insert image
    elements.append(get_image('data/logo.png', width=1.5*inch))
    elements.append(Spacer(1, 0.25 * inch))

    elements.append(Paragraph('<b>'+f"{title}"+'</b>', title_style))
    elements.append(Spacer(1, 0.4 * inch))


    elements.append(Paragraph('<b>Policy Background</b>', styles['Heading2']))
    # for subheadline in policy_background['content']:
    #     elements.append(Paragraph("<b>"+subheadline+"</b>"))
    #     for bullet in subheadline["content"]:
    #         bullet_style = ParagraphStyle(name='Bullet', leftIndent=20, bulletIndent=10, bulletFontName='Symbol')
    #         elements.append(Paragraph('• ' + bullet['text'], bullet_style))

    json_object = json.loads(policy_background)

    for section, subsections in json_object.items():
        elements.append(Paragraph("<b>"+section+"</b>"))
        for subsection in subsections:
            for k, v in subsection.items():  # Use items() instead of item()
                bullet_style = ParagraphStyle(name='Bullet', leftIndent=20, bulletIndent=10, bulletFontName='Symbol')
                elements.append(Paragraph('• ' + v, bullet_style))
                
    elements.append(Spacer(1, 0.25 * inch))

    for section_title, text_item in zip(section_titles, explanations):
        elements.append(Paragraph('<b>'+section_title+' :''</b>', styles['Heading2']))
        text_chunks = text_item.split('Subsection')  # Assuming each chunk is separated by double line breaks
        for index, chunk in enumerate(text_chunks):
            # Skip empty chunks
            if not chunk.strip():
                continue
            # Add bullet for subsequent chunks
            if index > 0:
                bullet_style = ParagraphStyle(name='Bullet', leftIndent=20, bulletIndent=10, bulletFontName='Symbol')
                elements.append(Paragraph('• ' + chunk.strip(), bullet_style))
            else:
                elements.append(Paragraph(chunk.strip(), styles['Normal']))  # First chunk without bullet
                elements.append(Spacer(1, 0.25 * inch))
        
        elements.append(Spacer(1, 0.25 * inch))
    
    doc.build(elements)

#######################################################
#### Explanatory note: Policy background functions ####
#######################################################

def policy_background_initial_prompt(client = anthropic_client):
    system_prompt = """
    You are a policy expert, with a speciality in writing background information for legislation for the UK government. Here is some guidance on how you should write policy backgrounds.

    Explanatory Notes were introduced in 1999 to go with every Bill which passes through Parliament. The notes are designed to assist readers who do not have legal training and are unfamiliar with the subject matter of the bill.
    Please note it should not explain the orginal legislation but reiterate it in simpler language, but still detailed.

    A useful policy background might cover the following:
    1)  Purpose – what are the objectives of the measures?
    2)  Context – what is the current position, the size and nature of the problem it is addressing?
    3)  Effects – what will be the effect on any target group, numbers affected and how are they affected?
    4)  Evidence – why is this solution likely to achieve the policy objective, or the degree to which it will impact?
    5)  Significance – whether the change is politically or legally important?

    Feel free to amend information you have from the UK legal system and UK new in relation to the issue.
    See below an example. The first text is primary legislation, the second its correspoining explanatory note:

    Primary legislation:
    Changes to legislation: There are currently no known outstanding
    effects for the Fraud Act 2006. (See end of Document for details)
    Fraud Act 2006
    2006 CHAPTER 35
    An Act to make provision for, and in connection with, criminal liability for fraud and
    obtaining services dishonestly. [8th November 2006]
    BE IT ENACTED by the Queen's most Excellent Majesty, by and with the advice and consent of
    the Lords Spiritual and Temporal, and Commons, in this present Parliament assembled, and by
    the authority of the same, as follows:—
    Fraud
    1 Fraud
    (1) A person is guilty of fraud if he is in breach of any of the sections listed in
    subsection (2) (which provide for different ways of committing the offence).
    (2) The sections are—
    (a) section 2 (fraud by false representation),
    (b) section 3 (fraud by failing to disclose information), and
    (c) section 4 (fraud by abuse of position).
    (3) A person who is guilty of fraud is liable—
    (a) on summary conviction, to imprisonment for a term not exceeding [F1the
    general limit in a magistrates’ court] or to a fine not exceeding the statutory
    maximum (or to both);
    (b) on conviction on indictment, to imprisonment for a term not exceeding 10
    years or to a fine (or to both).
    (4) Subsection (3)(a) applies in relation to Northern Ireland as if the reference to 12
    months were a reference to 6 months.
    2 Fraud Act 2006 (c. 35)
    Document Generated: 2023-04-24
    Changes to legislation: There are currently no known outstanding
    effects for the Fraud Act 2006. (See end of Document for details)
    Textual Amendments
    F1 Words in s. 1(3)(a) (and, by implication, the same words in s. 1(4)) substituted (7.2.2023 at 12.00
    p.m.) by virtue of The Judicial Review and Courts Act 2022 (Magistrates’ Court Sentencing Powers)
    Regulations 2023 (S.I. 2023/149), regs. 1(2), 2(1), Sch. Pt. 1
    2 Fraud by false representation
    (1) A person is in breach of this section if he—
    (a) dishonestly makes a false representation, and
    (b) intends, by making the representation—
    (i) to make a gain for himself or another, or
    (ii) to cause loss to another or to expose another to a risk of loss.
    (2) A representation is false if—
    (a) it is untrue or misleading, and
    (b) the person making it knows that it is, or might be, untrue or misleading.
    (3) “Representation” means any representation as to fact or law, including a representation
    as to the state of mind of—
    (a) the person making the representation, or
    (b) any other person.
    (4) A representation may be express or implied.
    (5) For the purposes of this section a representation may be regarded as made if it (or
    anything implying it) is submitted in any form to any system or device designed to
    receive, convey or respond to communications (with or without human intervention).
    3 Fraud by failing to disclose information
    A person is in breach of this section if he—
    (a) dishonestly fails to disclose to another person information which he is under
    a legal duty to disclose, and
    (b) intends, by failing to disclose the information—
    (i) to make a gain for himself or another, or
    (ii) to cause loss to another or to expose another to a risk of loss.
    4 Fraud by abuse of position
    (1) A person is in breach of this section if he—
    (a) occupies a position in which he is expected to safeguard, or not to act against,
    the financial interests of another person,
    (b) dishonestly abuses that position, and
    (c) intends, by means of the abuse of that position—
    (i) to make a gain for himself or another, or
    (ii) to cause loss to another or to expose another to a risk of loss.
    (2) A person may be regarded as having abused his position even though his conduct
    consisted of an omission rather than an act.
    Fraud Act 2006 (c. 35)
    Document Generated: 2023-04-24
    3
    Changes to legislation: There are currently no known outstanding
    effects for the Fraud Act 2006. (See end of Document for details)
    5 “Gain” and “loss”
    (1) The references to gain and loss in sections 2 to 4 are to be read in accordance with
    this section.
    (2) “Gain” and “loss”—
    (a) extend only to gain or loss in money or other property;
    (b) include any such gain or loss whether temporary or permanent;
    and “property” means any property whether real or personal (including things in action
    and other intangible property).
    (3) “Gain” includes a gain by keeping what one has, as well as a gain by getting what
    one does not have.
    (4) “Loss” includes a loss by not getting what one might get, as well as a loss by parting
    with what one has.
    6 Possession etc. of articles for use in frauds
    (1) A person is guilty of an offence if he has in his possession or under his control any
    article for use in the course of or in connection with any fraud.
    (2) A person guilty of an offence under this section is liable—
    (a) on summary conviction, to imprisonment for a term not exceeding [F2the
    general limit in a magistrates’ court] or to a fine not exceeding the statutory
    maximum (or to both);
    (b) on conviction on indictment, to imprisonment for a term not exceeding 5 years
    or to a fine (or to both).
    (3) Subsection (2)(a) applies in relation to Northern Ireland as if the reference to 12
    months were a reference to 6 months.
    Textual Amendments
    F2 Words in s. 6(2)(a) (and, by implication, the same words in s. 6(3)) substituted (7.2.2023 at 12.00 p.m.)
    by The Judicial Review and Courts Act 2022 (Magistrates’ Court Sentencing Powers) Regulations
    2023 (S.I. 2023/149), regs. 1(2), 2(1), Sch. Pt. 1
    7 Making or supplying articles for use in frauds
    (1) A person is guilty of an offence if he makes, adapts, supplies or offers to supply any
    article—
    (a) knowing that it is designed or adapted for use in the course of or in connection
    with fraud, or
    (b) intending it to be used to commit, or assist in the commission of, fraud.
    (2) A person guilty of an offence under this section is liable—
    (a) on summary conviction, to imprisonment for a term not exceeding [F3the
    general limit in a magistrates’ court] or to a fine not exceeding the statutory
    maximum (or to both);
    (b) on conviction on indictment, to imprisonment for a term not exceeding 10
    years or to a fine (or to both).
    4 Fraud Act 2006 (c. 35)
    Document Generated: 2023-04-24
    Changes to legislation: There are currently no known outstanding
    effects for the Fraud Act 2006. (See end of Document for details)
    (3) Subsection (2)(a) applies in relation to Northern Ireland as if the reference to 12
    months were a reference to 6 months.
    Textual Amendments
    F3 Words in s. 7(2)(a) (and, by implication, the same words in s. 7(3)) substituted (7.2.2023 at 12.00 p.m.)
    by The Judicial Review and Courts Act 2022 (Magistrates’ Court Sentencing Powers) Regulations
    2023 (S.I. 2023/149), regs. 1(2), 2(1), Sch. Pt. 1
    8 “Article”
    (1) For the purposes of—
    (a) sections 6 and 7, and
    (b) the provisions listed in subsection (2), so far as they relate to articles for use
    in the course of or in connection with fraud,
    “article” includes any program or data held in electronic form.
    (2) The provisions are—
    (a) section 1(7)(b) of the Police and Criminal Evidence Act 1984 (c. 60),
    (b) section 2(8)(b) of the Armed Forces Act 2001 (c. 19), and
    (c) Article 3(7)(b) of the Police and Criminal Evidence (Northern Ireland) Order
    1989 (S.I. 1989/1341 (N.I. 12));
    (meaning of “prohibited articles” for the purposes of stop and search powers).
    9 Participating in fraudulent business carried on by sole trader etc.
    (1) A person is guilty of an offence if he is knowingly a party to the carrying on of a
    business to which this section applies.
    (2) This section applies to a business which is carried on—
    (a) by a person who is outside the reach of [F4section 993 of the Companies Act
    2006] (offence of fraudulent trading), and
    (b) with intent to defraud creditors of any person or for any other fraudulent
    purpose.
    (3) The following are within the reach of [F5that section]—
    (a) a company [F6(as defined in section 1(1) of the Companies Act 2006)];
    (b) a person to whom that section applies (with or without adaptations or
    modifications) as if the person were a company;
    (c) a person exempted from the application of that section.
    (4) F7
    . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
    (5) “Fraudulent purpose” has the same meaning as in [F8that section].
    (6) A person guilty of an offence under this section is liable—
    (a) on summary conviction, to imprisonment for a term not exceeding [F9the
    general limit in a magistrates’ court] or to a fine not exceeding the statutory
    maximum (or to both);
    Fraud Act 2006 (c. 35)
    Document Generated: 2023-04-24
    5
    Changes to legislation: There are currently no known outstanding
    effects for the Fraud Act 2006. (See end of Document for details)
    (b) on conviction on indictment, to imprisonment for a term not exceeding 10
    years or to a fine (or to both).
    (7) Subsection (6)(a) applies in relation to Northern Ireland as if the reference to 12
    months were a reference to 6 months.
    Textual Amendments
    F4 Words in s. 9(2)(a) substituted (1.10.2007 with application as mentioned in Sch. 4 para. 111(6) of
    the amending S.I.) by virtue of The Companies Act 2006 (Commencement No. 3, Consequential
    Amendments, Transitional Provisions and Savings) Order 2007 (S.I. 2007/2194), arts. 1(3)(a), 10(1),
    Sch. 4 para. 111(2) (with art. 12)
    F5 Words in s. 9(3) substituted (1.10.2007 with application as mentioned in Sch. 4 para. 111(6) of the
    amending S.I.) by The Companies Act 2006 (Commencement No. 3, Consequential Amendments,
    Transitional Provisions and Savings) Order 2007 (S.I. 2007/2194), arts. 1(3)(a), 10(1), Sch. 4 para.
    111(3)(a) (with art. 12)
    F6 Words in s. 9(3)(a) substituted (1.10.2009) by The Companies Act 2006 (Consequential Amendments,
    Transitional Provisions and Savings) Order 2009 (S.I. 2009/1941), art. 1(2), Sch. 1 para. 257 (with art.
    10)
    F7 S. 9(4) repealed (1.10.2007 with application as mentioned in Sch. 4 para. 111(6) of the amending
    S.I.) by The Companies Act 2006 (Commencement No. 3, Consequential Amendments, Transitional
    Provisions and Savings) Order 2007 (S.I. 2007/2194), arts. 1(3)(a), 10(1)(3), Sch. 4 para. 111(4), Sch.
    5 (with art. 12)
    F8 Words in s. 9(5) substituted (1.10.2007 with application as mentioned in Sch. 4 para. 111(6) of the
    amending S.I.) by The Companies Act 2006 (Commencement No. 3, Consequential Amendments,
    Transitional Provisions and Savings) Order 2007 (S.I. 2007/2194), arts. 1(3)(a), 10(1), Sch. 4 para.
    111(5) (with art. 12)
    F9 Words in s. 9(6)(a) (and, by implication, the same words in s. 9(7)) substituted (7.2.2023 at 12.00 p.m.)
    by The Judicial Review and Courts Act 2022 (Magistrates’ Court Sentencing Powers) Regulations
    2023 (S.I. 2023/149), regs. 1(2), 2(1), Sch. Pt. 1
    F1010 Participating in fraudulent business carried on by company etc.: penalty
    . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
    Textual Amendments
    F10 S. 10 repealed (1.10.2009) by The Companies Act 2006 (Consequential Amendments, Transitional
    Provisions and Savings) Order 2009 (S.I. 2009/1941), art. 1(2), Sch. 2 (with art. 10)
    Obtaining services dishonestly
    11 Obtaining services dishonestly
    (1) A person is guilty of an offence under this section if he obtains services for himself
    or another—
    (a) by a dishonest act, and
    (b) in breach of subsection (2).
    (2) A person obtains services in breach of this subsection if—
    6 Fraud Act 2006 (c. 35)
    Document Generated: 2023-04-24
    Changes to legislation: There are currently no known outstanding
    effects for the Fraud Act 2006. (See end of Document for details)
    (a) they are made available on the basis that payment has been, is being or will
    be made for or in respect of them,
    (b) he obtains them without any payment having been made for or in respect of
    them or without payment having been made in full, and
    (c) when he obtains them, he knows—
    (i) that they are being made available on the basis described in
    paragraph (a), or
    (ii) that they might be,
    but intends that payment will not be made, or will not be made in full.
    (3) A person guilty of an offence under this section is liable—
    (a) on summary conviction, to imprisonment for a term not exceeding [F11the
    general limit in a magistrates’ court] or to a fine not exceeding the statutory
    maximum (or to both);
    (b) on conviction on indictment, to imprisonment for a term not exceeding 5 years
    or to a fine (or to both).
    (4) Subsection (3)(a) applies in relation to Northern Ireland as if the reference to 12
    months were a reference to 6 months.
    Textual Amendments
    F11 Words in s. 11(3)(a) (and, by implication, the same words in s. 11(4)) substituted (7.2.2023 at
    12.00 p.m.) by The Judicial Review and Courts Act 2022 (Magistrates’ Court Sentencing Powers)
    Regulations 2023 (S.I. 2023/149), regs. 1(2), 2(1), Sch. Pt. 1
    Supplementary
    12 Liability of company officers for offences by company
    (1) Subsection (2) applies if an offence under this Act is committed by a body corporate.
    (2) If the offence is proved to have been committed with the consent or connivance of—
    (a) a director, manager, secretary or other similar officer of the body corporate, or
    (b) a person who was purporting to act in any such capacity,
    he (as well as the body corporate) is guilty of the offence and liable to be proceeded
    against and punished accordingly.
    (3) If the affairs of a body corporate are managed by its members, subsection (2) applies
    in relation to the acts and defaults of a member in connection with his functions of
    management as if he were a director of the body corporate.
    13 Evidence
    (1) A person is not to be excused from—
    (a) answering any question put to him in proceedings relating to property, or
    (b) complying with any order made in proceedings relating to property,
    on the ground that doing so may incriminate him or his spouse or civil partner of an
    offence under this Act or a related offence.
    Fraud Act 2006 (c. 35)
    Document Generated: 2023-04-24
    7
    Changes to legislation: There are currently no known outstanding
    effects for the Fraud Act 2006. (See end of Document for details)
    (2) But, in proceedings for an offence under this Act or a related offence, a statement or
    admission made by the person in—
    (a) answering such a question, or
    (b) complying with such an order,
    is not admissible in evidence against him or (unless they married or became civil
    partners after the making of the statement or admission) his spouse or civil partner.
    (3) “Proceedings relating to property” means any proceedings for—
    (a) the recovery or administration of any property,
    (b) the execution of a trust, or
    (c) an account of any property or dealings with property,
    and “property” means money or other property whether real or personal (including
    things in action and other intangible property).
    (4) “Related offence” means—
    (a) conspiracy to defraud;
    (b) any other offence involving any form of fraudulent conduct or purpose.
    14 Minor and consequential amendments etc.
    (1) Schedule 1 contains minor and consequential amendments.
    (2) Schedule 2 contains transitional provisions and savings.
    (3) Schedule 3 contains repeals and revocations.
    15 Commencement and extent
    (1) This Act (except this section and section 16) comes into force on such day as the
    Secretary of State may appoint by an order made by statutory instrument; and different
    days may be appointed for different purposes.
    (2) Subject to subsection (3), sections 1 to 9 and 11 to 13 extend to England and Wales
    and Northern Ireland only.
    (3) Section 8, so far as it relates to the Armed Forces Act 2001 (c. 19), extends to any
    place to which that Act extends.
    (4) Any amendment in section 10 or Schedule 1, and any related provision in section 14
    or Schedule 2 or 3, extends to any place to which the provision which is the subject
    of the amendment extends.
    Subordinate Legislation Made
    P1 S. 15 power fully exercised: 15.1.2007 appointed for specified provisions by {S.I. 2006/3200}, art. 2
    16 Short title
    This Act may be cited as the Fraud Act 2006.
    8 Fraud Act 2006 (c. 35)
    SCHEDULE 1 – Minor and consequential amendments
    Document Generated: 2023-04-24
    Changes to legislation: There are currently no known outstanding
    effects for the Fraud Act 2006. (See end of Document for details)
    S C H E D U L E S
    SCHEDULE 1 Section 14(1)
    MINOR AND CONSEQUENTIAL AMENDMENTS
    Abolition of various deception offences
    1 Omit the following provisions—
    (a) in the Theft Act 1968 (c. 60)—
    (i) section 15 (obtaining property by deception);
    (ii) section 15A (obtaining a money transfer by deception);
    (iii) section 16 (obtaining pecuniary advantage by deception);
    (iv) section 20(2) (procuring the execution of a valuable security by
    deception);
    (b) in the Theft Act 1978 (c. 31)—
    (i) section 1 (obtaining services by deception);
    (ii) section 2 (evasion of liability by deception);
    (c) in the Theft Act (Northern Ireland) 1969 (c. 16 (N.I.))—
    (i) section 15 (obtaining property by deception);
    (ii) section 15A (obtaining a money transfer by deception);
    (iii) section 16 (obtaining pecuniary advantage by deception);
    (iv) section 19(2) (procuring the execution of a valuable security by
    deception);
    (d) in the Theft (Northern Ireland) Order 1978 (S.I. 1978/1407 (N.I. 23))—
    (i) Article 3 (obtaining services by deception);
    (ii) Article 4 (evasion of liability by deception).
    Visiting Forces Act 1952 (c. 67)
    2 In the Schedule (offences referred to in section 3 of the 1952 Act), in paragraph 3
    (meaning of “offence against property”), after sub-paragraph (l) insert—
    “(m) the Fraud Act 2006.”
    Theft Act 1968 (c. 60)
    3 Omit section 15B (section 15A: supplementary).
    4 In section 18(1) (liability of company officers for offences by company under
    section 15, 16 or 17), omit “ 15, 16 or ”.
    5 In section 20(3) (suppression etc. of documents—interpretation), omit “deception”
    has the same meaning as in section 15 of this Act, and ”.
    Fraud Act 2006 (c. 35)
    SCHEDULE 1 – Minor and consequential amendments
    Document Generated: 2023-04-24
    9
    Changes to legislation: There are currently no known outstanding
    effects for the Fraud Act 2006. (See end of Document for details)
    6 (1) In section 24(4) (meaning of “stolen goods”) for “in the circumstances described
    in section 15(1) of this Act” substitute “
    , subject to subsection (5) below, by fraud
    (within the meaning of the Fraud Act 2006) ”.
    (2) After section 24(4) insert—
    “(5) Subsection (1) above applies in relation to goods obtained by fraud as if—
    (a) the reference to the commencement of this Act were a reference to
    the commencement of the Fraud Act 2006, and
    (b) the reference to an offence under this Act were a reference to an
    offence under section 1 of that Act.
    ”
    7 (1) In section 24A (dishonestly retaining a wrongful credit), omit subsections (3) and
    (4) and after subsection (2) insert—
    “(2A) A credit to an account is wrongful to the extent that it derives from—
    (a) theft;
    (b) blackmail;
    (c) fraud (contrary to section 1 of the Fraud Act 2006); or
    (d) stolen goods.”
    (2) In subsection (7), for “subsection (4)” substitute “ subsection (2A) ”.
    (3) For subsection (9) substitute—
    “(9) “Account” means an account kept with—
    (a) a bank;
    (b) a person carrying on a business which falls within subsection (10)
    below; or
    (c) an issuer of electronic money (as defined for the purposes of Part 2
    of the Financial Services and Markets Act 2000).
    (10) A business falls within this subsection if—
    (a) in the course of the business money received by way of deposit is
    lent to others; or
    (b) any other activity of the business is financed, wholly or to any
    material extent, out of the capital of or the interest on money
    received by way of deposit.
    (11) References in subsection (10) above to a deposit must be read with—
    (a) section 22 of the Financial Services and Markets Act 2000;
    (b) any relevant order under that section; and
    (c) Schedule 2 to that Act;
    but any restriction on the meaning of deposit which arises from the identity
    of the person making it is to be disregarded.
    (12) For the purposes of subsection (10) above—
    (a) all the activities which a person carries on by way of business shall
    be regarded as a single business carried on by him; and
    (b) “money” includes money expressed in a currency other than
    sterling.”
    8 In section 25 (going equipped for burglary, theft or cheat)—
    10 Fraud Act 2006 (c. 35)
    SCHEDULE 1 – Minor and consequential amendments
    Document Generated: 2023-04-24
    Changes to legislation: There are currently no known outstanding
    effects for the Fraud Act 2006. (See end of Document for details)
    (a) in subsections (1) and (3) for “burglary, theft or cheat” substitute “ burglary
    or theft ”, and
    (b) in subsection (5) omit “
    , and “cheat” means an offence under section 15
    of this Act ”.
    Theft Act (Northern Ireland) 1969 (c. 16 (N.I.))
    9 Omit section 15B (section 15A: supplementary).
    10 In section 19(3) (suppression etc. of documents—interpretation), omit “deception”
    has the same meaning as in section 15, and ”.
    11 (1) In section 23(5) (meaning of “stolen goods”) for “in the circumstances described in
    section 15(1)” substitute “ , subject to subsection (6), by fraud (within the meaning
    of the Fraud Act 2006) ”.
    (2) After section 23(5) insert—
    “(6) Subsection (1) applies in relation to goods obtained by fraud as if—
    (a) the reference to the commencement of this Act were a reference to
    the commencement of the Fraud Act 2006, and
    (b) the reference to an offence under this Act were a reference to an
    offence under section 1 of that Act.
    ”
    12 (1) In section 23A (dishonestly retaining a wrongful credit), omit subsections (3) and
    (4) and after subsection (2) insert—
    “(2A) A credit to an account is wrongful to the extent that it derives from—
    (a) theft;
    (b) blackmail;
    (c) fraud (contrary to section 1 of the Fraud Act 2006); or
    (d) stolen goods.”
    (2) In subsection (7), for “subsection (4)” substitute “ subsection (2A) ”.
    (3) For subsection (9) substitute—
    “(9) “Account” means an account kept with—
    (a) a bank;
    (b) a person carrying on a business which falls within subsection (10); or
    (c) an issuer of electronic money (as defined for the purposes of Part 2
    of the Financial Services and Markets Act 2000).
    (10) A business falls within this subsection if—
    (a) in the course of the business money received by way of deposit is
    lent to others; or
    (b) any other activity of the business is financed, wholly or to any
    material extent, out of the capital of or the interest on money
    received by way of deposit.
    (11) References in subsection (10) to a deposit must be read with—
    (a) section 22 of the Financial Services and Markets Act 2000;
    (b) any relevant order under that section; and
    (c) Schedule 2 to that Act;
    Fraud Act 2006 (c. 35)
    SCHEDULE 1 – Minor and consequential amendments
    Document Generated: 2023-04-24
    11
    Changes to legislation: There are currently no known outstanding
    effects for the Fraud Act 2006. (See end of Document for details)
    but any restriction on the meaning of deposit which arises from the identity
    of the person making it is to be disregarded.
    (12) For the purposes of subsection (10)—
    (a) all the activities which a person carries on by way of business shall
    be regarded as a single business carried on by him; and
    (b) “money” includes money expressed in a currency other than
    sterling.”
    13 In section 24 (going equipped for burglary, theft or cheat)—
    (a) in subsections (1) and (3), for “burglary, theft or cheat” substitute “ burglary
    or theft ”, and
    (b) in subsection (5), omit “
    , and “cheat” means an offence under section 15 ”
    .
    Theft Act 1978 (c. 31)
    14 In section 4 (punishments), omit subsection (2)(a).
    15 In section 5 (supplementary), omit subsection (1).
    Theft (Northern Ireland) Order 1978 (S.I. 1978/1407 (N.I. 23))
    16 In Article 6 (punishments), omit paragraph (2)(a).
    17 In Article 7 (supplementary), omit paragraph (1).
    Limitation Act 1980 (c. 58)
    18 In section 4 (special time limit in case of theft), for subsection (5)(b) substitute—
    “(b) obtaining any chattel (in England and Wales or elsewhere) by—
    (i) blackmail (within the meaning of section 21 of the Theft
    Act 1968), or
    (ii) fraud (within the meaning of the Fraud Act 2006);”.
    Finance Act 1982 (c. 39)
    19 In section 11(1) (powers of Commissioners with respect to agricultural levies), for
    “or the Theft (Northern Ireland) Order 1978,” substitute “ , the Theft (Northern
    Ireland) Order 1978 or the Fraud Act 2006 ”.
    Nuclear Material (Offences) Act 1983 (c. 18)
    20 In section 1 (extended scope of certain offences), in subsection (1)(d), omit “ 15
    or ” (in both places).
    Police and Criminal Evidence Act 1984 (c. 60)
    21 In section 1 (power of constable to stop and search persons, vehicles etc.), in
    subsection (8), for paragraph (d) substitute—
    “(d) fraud (contrary to section 1 of the Fraud Act 2006).”
    12 Fraud Act 2006 (c. 35)
    SCHEDULE 1 – Minor and consequential amendments
    Document Generated: 2023-04-24
    Changes to legislation: There are currently no known outstanding
    effects for the Fraud Act 2006. (See end of Document for details)
    Limitation (Northern Ireland) Order 1989 (S.I. 1989/1339 (N.I. 11))
    22 In Article 18 (special time limit in case of theft), for paragraph (5)(b) substitute—
    “(b) obtaining any chattel (in Northern Ireland or elsewhere) by—
    (i) blackmail (within the meaning of section 20 of the Theft
    Act (Northern Ireland) 1969), or
    (ii) fraud (within the meaning of the Fraud Act 2006);”.
    Police and Criminal Evidence (Northern Ireland) Order 1989 (S.I. 1989/1341 (N.I. 12))
    23 In Article 3 (power of constable to stop and search persons, vehicles etc.), in
    paragraph (8), for sub-paragraph (d) substitute—
    “(d) fraud (contrary to section 1 of the Fraud Act 2006).”
    Criminal Justice Act 1993 (c. 36)
    24 (1) In section 1(2) (Group A offences), omit the entries in paragraph (a) relating to
    sections 15, 15A, 16 and 20(2) of the Theft Act 1968.
    (2) Omit section 1(2)(b).
    (3) Before section 1(2)(c) insert—
    “(bb) an offence under any of the following provisions of the Fraud Act
    2006—
    (i) section 1 (fraud);
    (ii) section 6 (possession etc. of articles for use in frauds);
    (iii) section 7 (making or supplying articles for use in frauds);
    (iv) section 9 (participating in fraudulent business carried on by
    sole trader etc.);
    (v) section 11 (obtaining services dishonestly).
    ”
    25 (1) Amend section 2 (jurisdiction in respect of Group A offences) as follows.
    (2) In subsection (1), after “means” insert “ (subject to subsection (1A)) ”.
    (3) After subsection (1) insert—
    “(1A) In relation to an offence under section 1 of the Fraud Act 2006 (fraud),
    “relevant event” includes—
    (a) if the fraud involved an intention to make a gain and the gain
    occurred, that occurrence;
    (b) if the fraud involved an intention to cause a loss or to expose another
    to a risk of loss and the loss occurred, that occurrence.”
    Criminal Justice (Northern Ireland) Order 1994 (S.I. 1994/2795 (N.I. 15))
    26 In Article 14 (compensation orders), in paragraphs (3) and (4)(a) for “or Article 172
    of the Road Traffic (Northern Ireland) Order 1981” substitute “ , Article 172 of the
    Road Traffic (Northern Ireland) Order 1981 or the Fraud Act 2006 ”
    .
    Fraud Act 2006 (c. 35)
    SCHEDULE 1 – Minor and consequential amendments
    Document Generated: 2023-04-24
    13
    Changes to legislation: There are currently no known outstanding
    effects for the Fraud Act 2006. (See end of Document for details)
    Criminal Justice (Northern Ireland) Order 1996 (S.I. 1996/3160 (N.I. 24))
    27 (1) In Article 38(2) (Group A offences), omit the entries in sub-paragraph (a) relating to
    sections 15, 15A, 16 and 19(2) of the Theft Act (Northern Ireland) 1969.
    (2) Omit Article 38(2)(b).
    (3) Before Article 38(2)(c) insert—
    “(bb) an offence under any of the following provisions of the Fraud Act
    2006—
    (i) section 1 (fraud);
    (ii) section 6 (possession etc. of articles for use in frauds);
    (iii) section 7 (making or supplying articles for use in frauds);
    (iv) section 9 (participating in fraudulent business carried on by
    sole trader etc.);
    (v) section 11 (obtaining services dishonestly).
    ”
    28 (1) Amend Article 39 (jurisdiction in respect of Group A offences) as follows.
    (2) In paragraph (1), after “means” insert “ (subject to paragraph (1A)) ”.
    (3) After paragraph (1) insert—
    “(1A) In relation to an offence under section 1 of the Fraud Act 2006 (fraud),
    “relevant event” includes—
    (a) if the fraud involved an intention to make a gain and the gain
    occurred, that occurrence;
    (b) if the fraud involved an intention to cause a loss or to expose another
    to a risk of loss and the loss occurred, that occurrence.”
    Powers of Criminal Courts (Sentencing) Act 2000 (c. 6)
    F1229 . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
    Textual Amendments
    F12 Sch. 1 para. 29 repealed (1.12.2020) by Sentencing Act 2020 (c. 17), s. 416(1), Sch. 28 (with s. 413(4)(5),
    416(7), Sch. 27); S.I. 2020/1236, reg. 2
    Modifications etc. (not altering text)
    C1 Sch. 1 para. 29 modified (1.12.2020 immediately before the consolidation date (see 2020 c. 9, ss. 3, 5(2)
    (3) and 2020 c. 17, ss. 2, 416)) by Sentencing (Pre-consolidation Amendments) Act 2020 (c. 9), ss. 1,
    5(2)(3); S.I. 2012/1236, reg. 2
    Terrorism Act 2000 (c. 11)
    30 (1) In Schedule 9 (scheduled offences), in paragraph 10, at the end of sub-paragraph (d)
    insert “ and ” and omit paragraph (e).
    (2) After paragraph 22A of that Schedule insert—
    14 Fraud Act 2006 (c. 35)
    SCHEDULE 1 – Minor and consequential amendments
    Document Generated: 2023-04-24
    Changes to legislation: There are currently no known outstanding
    effects for the Fraud Act 2006. (See end of Document for details)
    “Fraud Act 2006
    23 Offences under section 1 of the Fraud Act 2006 (fraud) subject to note
    2 below.
    ”
    (3) In note 2 to Part 1 of Schedule 9, for “paragraph 10(a), (c) or (e)” substitute “
    paragraph 10(a) or (c) or 23 ”.
    31 (1) In Schedule 12 (compensation), in paragraph 12(1), omit “ (within the meaning of
    section 15(4) of the Theft Act (Northern Ireland) 1969) ”.
    (2) After paragraph 12(1) of that Schedule insert—
    “(1A) “Deception” means any deception (whether deliberate or reckless) by
    words or conduct as to fact or as to law, including a deception as to the
    present intentions of the person using the deception or any other person.”
    Criminal Justice and Court Services Act 2000 (c. 43)
    32 (1) In Schedule 6 (trigger offences), in paragraph 1, omit the entry relating to section 15
    of the Theft Act 1968.
    (2) After paragraph 2 of Schedule 6 insert—
    “3 Offences under the following provisions of the Fraud Act 2006 are
    trigger offences—
    section 1 (fraud)
    section 6 (possession etc. of articles for use in frauds)
    section 7 (making or supplying articles for use in frauds).”
    Armed Forces Act 2001 (c. 19)
    33 In section 2(9) (definition of prohibited articles for purposes of powers to stop and
    search), for paragraph (d) substitute—
    “(d) fraud (contrary to section 1 of the Fraud Act 2006).”
    Licensing Act 2003 (c. 17)
    34 In Schedule 4 (personal licence: relevant offences), after paragraph 20 insert—
    “21 An offence under the Fraud Act 2006.
    ”
    Asylum and Immigration (Treatment of Claimants, etc.) Act 2004 (c. 19)
    35 (1) In section 14(2) (offences giving rise to immigration officer's power of arrest), omit
    paragraph “ (g)(ii) ” and “ (iii) ”, in paragraph “ (h) ”, “ 15, 16 ” and paragraphs
    (i) and (j).
    (2) After section 14(2)(h) insert—
    “(ha) an offence under either of the following provisions of the Fraud Act
    2006—
    (i) section 1 (fraud);
    (ii) section 11 (obtaining services dishonestly),
    ”
    .
    Fraud Act 2006 (c. 35)
    SCHEDULE 2 – Transitional provisions and savings
    Document Generated: 2023-04-24
    15
    Changes to legislation: There are currently no known outstanding
    effects for the Fraud Act 2006. (See end of Document for details)
    Serious Organised Crime and Police Act 2005 (c. 15)
    36 In section 76 (financial reporting orders: making), in subsection (3), for paragraphs
    (a) and (b) substitute—
    “(aa) an offence under either of the following provisions of the Fraud Act
    2006—
    (i) section 1 (fraud),
    (ii) section 11 (obtaining services dishonestly),
    ”
    .
    37 In section 78 (financial reporting orders: making in Northern Ireland), in
    subsection (3), for paragraphs (a) and (b) substitute—
    “(aa) an offence under either of the following provisions of the Fraud Act
    2006—
    (i) section 1 (fraud),
    (ii) section 11 (obtaining services dishonestly),
    ”
    .
    Gambling Act 2005 (c. 19)
    38 After paragraph 3 of Schedule 7 (relevant offences) insert—
    “3A An offence under the Fraud Act 2006.
    ”
    SCHEDULE 2 Section 14(2)
    TRANSITIONAL PROVISIONS AND SA VINGS
    Maximum term of imprisonment for offences under this Act
    1 In relation to an offence committed before [F132 May 2022], the references to [F14the
    general limit in a magistrates’ court] in sections 1(3)(a), 6(2)(a), 7(2)(a), 9(6)(a)
    and 11(3)(a) are to be read as references to 6 months.
    Textual Amendments
    F13 Words in Sch. 2 para. 1 substituted (28.4.2022) by The Criminal Justice Act 2003 (Commencement
    No. 33) and Sentencing Act 2020 (Commencement No. 2) Regulations 2022 (S.I. 2022/500), regs. 1(2),
    5(1), Sch. Pt. 1
    F14 Words in Sch. 2 para. 1 substituted (7.2.2023 at 12.00 p.m.) by The Judicial Review and Courts Act 2022
    (Magistrates’ Court Sentencing Powers) Regulations 2023 (S.I. 2023/149), regs. 1(2), 2(1), Sch. Pt. 1
    Increase in penalty for fraudulent trading
    2 Section 10 does not affect the penalty for any offence committed before that section
    comes into force.
    Abolition of deception offences
    3 (1) Paragraph 1 of Schedule 1 does not affect any liability, investigation, legal
    proceeding or penalty for or in respect of any offence partly committed before the
    commencement of that paragraph.
    16 Fraud Act 2006 (c. 35)
    SCHEDULE 2 – Transitional provisions and savings
    Document Generated: 2023-04-24
    Changes to legislation: There are currently no known outstanding
    effects for the Fraud Act 2006. (See end of Document for details)
    (2) An offence is partly committed before the commencement of paragraph 1 of
    Schedule 1 if—
    (a) a relevant event occurs before its commencement, and
    (b) another relevant event occurs on or after its commencement.
    (3) “Relevant event”
    , in relation to an offence, means any act, omission or other event
    (including any result of one or more acts or omissions) proof of which is required
    for conviction of the offence.
    Scope of offences relating to stolen goods under the Theft Act 1968 (c. 60)
    4 Nothing in paragraph 6 of Schedule 1 affects the operation of section 24 of the
    Theft Act 1968 in relation to goods obtained in the circumstances described in
    section 15(1) of that Act where the obtaining is the result of a deception made before
    the commencement of that paragraph.
    Dishonestly retaining a wrongful credit under the Theft Act 1968
    5 Nothing in paragraph 7 of Schedule 1 affects the operation of section 24A(7) and
    (8) of the Theft Act 1968 in relation to credits falling within section 24A(3) or (4)
    of that Act and made before the commencement of that paragraph.
    Scope of offences relating to stolen goods under
    the Theft Act (Northern Ireland) 1969 (c. 16 (N.I.))
    6 Nothing in paragraph 11 of Schedule 1 affects the operation of section 23 of the
    Theft Act (Northern Ireland) 1969 in relation to goods obtained in the circumstances
    described in section 15(1) of that Act where the obtaining is the result of a deception
    made before the commencement of that paragraph.
    Dishonestly retaining a wrongful credit under the Theft Act (Northern Ireland) 1969
    7 Nothing in paragraph 12 of Schedule 1 affects the operation of section 23A(7) and
    (8) of the Theft Act (Northern Ireland) 1969 in relation to credits falling within
    section 23A(3) or (4) of that Act and made before the commencement of that
    paragraph.
    Limitation periods under the Limitation Act 1980 (c. 58)
    8 Nothing in paragraph 18 of Schedule 1 affects the operation of section 4 of the
    Limitation Act 1980 in relation to chattels obtained in the circumstances described
    in section 15(1) of the Theft Act 1968 where the obtaining is a result of a deception
    made before the commencement of that paragraph.
    Limitation periods under the Limitation (Northern
    Ireland) Order 1989 (S.I. 1989/1339 (N.I. 11))
    9 Nothing in paragraph 22 of Schedule 1 affects the operation of Article 18 of the
    Limitation (Northern Ireland) Order 1989 in relation to chattels obtained in the
    circumstances described in section 15(1) of the Theft Act (Northern Ireland) 1969
    where the obtaining is a result of a deception made before the commencement of
    that paragraph.
    Fraud Act 2006 (c. 35)
    SCHEDULE 3 – Repeals and revocations
    Document Generated: 2023-04-24
    17
    Changes to legislation: There are currently no known outstanding
    effects for the Fraud Act 2006. (See end of Document for details)
    Scheduled offences under the Terrorism Act 2000 (c. 11)
    10 Nothing in paragraph 30 of Schedule 1 affects the operation of Part 7 of the
    Terrorism Act 2000 in relation to an offence under section 15(1) of the Theft Act
    (Northern Ireland) 1969 where the obtaining is a result of a deception made before
    the commencement of that paragraph.
    Powers of arrest under Asylum and Immigration
    (Treatment of Claimants, etc.) Act 2004 (c. 19)
    11 (1) Nothing in paragraph 35 of Schedule 1 affects the power of arrest conferred by
    section 14 of the Asylum and Immigration (Treatment of Claimants, etc.) Act 2004 in
    relation to an offence partly committed before the commencement of that paragraph.
    (2) An offence is partly committed before the commencement of paragraph 35 of
    Schedule 1 if—
    (a) a relevant event occurs before its commencement, and
    (b) another relevant event occurs on or after its commencement.
    (3) “Relevant event”
    , in relation to an offence, means any act, omission or other event
    (including any result of one or more acts or omissions) proof of which is required
    for conviction of the offence.
    SCHEDULE 3 Section 14(3)
    REPEALS AND REVOCATIONS
    Title and number Extent of repeal or revocation
    Theft Act 1968 (c. 60) Sections 15, 15A, 15B and 16.
    In section 18(1), “15, 16 or”.
    Section 20(2).
    In section 20(3), “ “deception” has the same
    meaning as in section 15 of this Act, and”.
    Section 24A(3) and (4).
    In section 25(5), “, and “cheat” means an
    offence under section 15 of this Act”
    .
    Theft Act (Northern Ireland) 1969 (c. 16
    (N.I.))
    Sections 15, 15A, 15B and 16.
    Section 19(2).
    In section 19(3), “ “deception” has the same
    meaning as in section 15, and”.
    Section 23A(3) and (4).
    In section 24(5), “, and “cheat” means an
    offence under section 15”
    .
    Theft Act 1978 (c. 31) Sections 1 and 2.
    Section 4(2)(a).
    Section 5(1).
    Theft (Northern Ireland) Order 1978 (S.I.
    1978/1407 (N.I. 23))
    Articles 3 and 4.
    Article 6(2)(a).
    Article 7(1).
    18 Fraud Act 2006 (c. 35)
    SCHEDULE 3 – Repeals and revocations
    Document Generated: 2023-04-24
    Changes to legislation: There are currently no known outstanding
    effects for the Fraud Act 2006. (See end of Document for details)
    Nuclear Material (Offences) Act 1983 (c. 18) In section 1(1)(d), “15 or” (in both places).
    Criminal Justice Act 1993 (c. 36) In section 1(2), the entries in paragraph (a)
    relating to sections 15, 15A, 16 and 20(2) of
    the Theft Act 1968.
    Section 1(2)(b).
    Theft (Amendment) Act 1996 (c. 62) Sections 1, 3(2) and 4.
    Criminal Justice (Northern Ireland) Order
    1996 (S.I. 1996/3160 (N.I. 24))
    In Article 38(2), the entries in sub-
    paragraph (a) relating to sections 15, 15A, 16
    and 19(2) of the Theft Act (Northern Ireland)
    1969.
    Article 38(2)(b).
    Theft (Amendment) (Northern Ireland) Order
    1997 (S.I. 1997/277 (N.I. 3))
    Articles 3, 5(2) and 6.
    Terrorism Act 2000 (c. 11) In Schedule 9, paragraph 10(e).
    In Schedule 12, in paragraph 12(1), “(within
    the meaning of section 15(4) of the Theft Act
    (Northern Ireland) 1969)”.
    Criminal Justice and Court Services Act 2000
    (c. 43)
    In Schedule 6, in paragraph 1, the entry
    relating to section 15 of the Theft Act 1968.
    Asylum and Immigration (Treatment of
    Claimants, etc.) Act 2004 (c. 19)
    In section 14(2), paragraph (g)(ii) and (iii),
    in paragraph (h), “15, 16” and paragraphs (i)
    and (j).
    Fraud Act 2006 (c. 35)
    Document Generated: 2023-04-24
    19
    Changes to legislation:
    There are currently no known outstanding effects for the Fraud Act 2006.

    ############################
    Explanatory Note:
    ############################
    These notes refer to the Fraud Act 2006 (c.35)
    which received Royal Assent on 8 November 2006
    FRAUD ACT 2006
    EXPLANATORY NOTES
    INTRODUCTION
    1. These explanatory notes relate to the Fraud Act 2006 which received Royal Assent on
    8 November 2006. They have been prepared by the Home Office in order to assist the
    reader in understanding the Act. They do not form part of the Act and have not been
    endorsed by Parliament.
    2. These notes need to be read in conjunction with the Act. They are not, and are not meant
    to be, a comprehensive description of the Act. So where a section does not seem to
    require any explanation, none is given.
    3. The Act extends to England, Wales and Northern Ireland. The Act does not extend to
    Scotland except section 10(1) which amends the Companies Act 1985.
    TERRITORIAL APPLICATION: WALES
    4. The Act applies to Wales as it does to the rest of the jurisdiction. It does not have any
    particular effect on the National Assembly for Wales.
    BACKGROUND
    5. The Government’s policy on the reform of the criminal law of fraud is largely based
    on the Law Commission’s Report on Fraud (Law Com No. 276, Cm 5560, 2002). The
    Law Commission’s report did not deal with the position in Northern Ireland (because
    the Law Commission is concerned with the law in England and Wales). Views on the
    Law Commission’s proposals were sought in the Government's consultation paper on
    Fraud Law Reform (May 2004). The Government’s Response to the views expressed
    in consultations was published on the Home Office website (www.homeoffice.gov.uk/
    documents/cons-fraud-law-reform) on 24 November 2004. A parallel consultation was
    also carried out in Northern Ireland and responses were broadly similar to those in
    England and Wales.
    6. The Law Commission’s report recommended that conspiracy to defraud should be
    abolished. The majority of those who responded on this point in the Home Office’s
    consultation were opposed to this on the basis of serious practical concerns about
    the ability to prosecute multiple offences in the largest and most serious cases of
    fraud and a desire to see how the new statutory offences worked in practice before
    abolishing conspiracy to defraud. There were also concerns that limitations on the scope
    of statutory conspiracy meant that certain types of secondary participation in fraud
    might still only be caught by the common law charge. So, in the light of the consultation,
    the Government concluded that immediate abolition of conspiracy to defraud would
    create considerable risks for the effective prosecution of fraud cases. The Government
    proposed to reassess whether there is a continuing need to retain conspiracy to defraud
    in the light of the operation of the new offences and the Law Commission’s impending
    report on encouraging and assisting crime. The Law Commission has now published its
    report on Inchoate Liability for Assisting and Encouraging Crime (Law Com No. 300,
    Cm 6878, 2006) and is due to publish a second, final, report dealing with secondary
    liability in late Autumn.

    Do not cover any of the legislation changes. Soley focus on the policy background.
    Do give this in one paragraph!

    """

    """#@title Initial user prompt"""

    user_prompt = """
        Acting as a policy expert, you will be asked to provide explanatory notes for a piece of legislation that is provided by the user.
        This document will have the following headings (as found in the example provided):
        Introduction
        Territorial Application
        Background
        Summary

        Each section will have numbered subheadings related to different key points made in the legislation document.

        When you first recieve the document, or text, you will be asked to read through and obtain the context of the document and all topics it relates to.
        Once you have obtained context from the document respond to this prompt with "Awaiting legislation document" and nothing else.
        """

    """#@title Claude initial call"""

    # Assume user_prompt and system_prompt are defined somewhere above this code
    messages = [
        {"role": "user", "content": user_prompt}
    ]

    # Simulating the API call to create a message
    # This is a pseudo-code example to show how the API call might look
    message = client.messages.create(
        model="claude-3-opus-20240229",
        max_tokens=1000,
        temperature=0.5,
        system=system_prompt,
        messages=messages
    )

    # Assuming 'message.content' returns a list of objects and each object has a 'text' attribute
    # Here, we consider the first object's text for simplicity
    if message.content:  # Check if content is not empty
        new_message_text = message.content[0].text  # Accessing the text attribute of the first content item

        # Append a new dictionary to the messages list with the role of "assistant" and the extracted text content
        messages.append({"role": "assistant", "content": new_message_text})

        # Print the content of the new message
        print(new_message_text)
    else:
        print("No content received from the API")

    initial_messages = messages

    return initial_messages, system_prompt



def extract_text(file_path):
    """
    Read files with text data from
    pdf, docx, txt or rtf file formats

    # Example usage
    text_from_pdf = extract_text('example.pdf')
    text_from_docx = extract_text('example.docx')
    text_from_txt = extract_text('example.txt')
    text_from_rtf = extract_text('example.rtf')
    """
    # Get the file extension
    file_extension = os.path.splitext(file_path)[1].lower()

    if file_extension == '.pdf':
        # Handle PDF files
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            text = ''
            for page in pdf_reader.pages:
                text += (page.extract_text() or '') + '\n'
        return text
    elif file_extension == '.docx':
        # Handle DOCX files
        doc = Document(file_path)
        text = '\n'.join([paragraph.text for paragraph in doc.paragraphs])
        return text
    elif file_extension == '.txt':
        # Handle TXT files
        with open(file_path, 'r', encoding='utf-8') as file:
            text = file.read()
        return text
    elif file_extension == '.rtf':
        # Handle RTF files
        from pyth.plugins.rtf15.reader import Rtf15Reader
        from pyth.plugins.plaintext.writer import PlaintextWriter
        with open(file_path, 'rb') as file:
            doc = Rtf15Reader.read(file)
        return PlaintextWriter.write(doc).getvalue()
    else:
        raise ValueError(f"Unsupported file type: {file_extension}")

def document_submission_message(file_path):
    # Call the function and print the extracted text
    extracted_text = extract_text(file_path)

    # Debugging - print text
    # print(extracted_text)

    document_submission_prompt = """
        The legislation document is included in this message beneath the dashed line.
        Please obtain the subject matter of this document and other relevant topics.

        With this information please return a search string for both the legislation.gov.uk database
        as well as the newscatcher API database.
        Use boolean logic to combine search terms together. Make sure that each search string only contains terms that are relevant search domains.
        Do not confine the subject matter within the boundaries of policy and regulation i.e "(skateboarding OR skateboard) AND (regulation OR licensing OR offences OR safety OR public order)" is incorrect.
        Do not put quotation marks (" or ') around individual search terms or words i.e "(skateboarding OR 'skating')" is incorrect.

        For the Newscatcher API search string, if combining two search terms using boolean logic, if one search term contains more than one word, use parentheses to group them.
        For example: skateboard OR (skateboard licensing offences)

        Please return your responses as a dictionary with headers as follows:

        api_responses = {
        "Legislation.gov.uk": {
            "search_string": "search string specific to Legislation.gov.uk",
            "description_of_domain": "description of domain used for querying legislation data this is the context that we wanted to search"
          },
        "Newscatcher API": {
            "search_string": "search string specific to Newsgrinder API",
            "description_of_domain": "description of domain used for querying news data this is the context that we wanted to search"
          }
        }
        ----------------------------------------------------------------------
    """ + extracted_text

    return document_submission_prompt

def document_submission_response(initial_messages, system_prompt, document_submission_prompt, client = anthropic_client):
    messages = initial_messages

    # Add user prompt
    messages.append({"role": "user", "content": document_submission_prompt})

    # print(messages)
    message = client.messages.create(
        model="claude-3-sonnet-20240229",
        max_tokens=4016,
        temperature=0.5,
        system=system_prompt,
        messages=messages
    )

    # Assuming 'message.content' returns a list of objects and each object has a 'text' attribute
    # Here, we consider the first object's text for simplicity
    if message.content:  # Check if content is not empty
        new_message_text = message.content[0].text  # Accessing the text attribute of the first content item

        # Append a new dictionary to the messages list with the role of "assistant" and the extracted text content
        messages.append({"role": "assistant", "content": new_message_text})

        search_strings = new_message_text

        # Print the content of the new message
        # print(new_message_text)
    else:
        print("No content received from the API")

    post_document_messages = messages

    return post_document_messages, search_strings

def extract_search_strings(search_strings):
    # Parsing the dictionary from the text block's text
    # Extracting the assignment part after the '=' sign
    api_responses_str = search_strings.split('=', 1)[1].strip()

    # Convert the string representation of dictionary to an actual dictionary
    api_responses = ast.literal_eval(api_responses_str)

    # Extract search strings
    legislation_search_string = api_responses["Legislation.gov.uk"]["search_string"]
    newscatcher_search_string = api_responses["Newscatcher API"]["search_string"]

    return legislation_search_string, newscatcher_search_string

def remove_unusual_characters(s):
    # Define the characters to remove
    remove_chars = ":',\"@;"
    
    # Create a translation table that maps each character to None
    # str.maketrans creates a mapping from characters to replacements
    # None means the character is to be removed
    trans_table = str.maketrans('', '', remove_chars)
    
    # Translate the string using the translation table
    return s.translate(trans_table)

def newscatcher_api_call(newscatcher_search_string):
    newscatcher = Newscatcher(
    api_key="9va0oLmndtTX_uqw9naX5VZLUJsW_9Oc",
    )

    # Catch syntax errors in search strings
    try:
        # [Get] Search By Author Request
        get_response = newscatcher.search.get(
            q=newscatcher_search_string,
            lang="en",
            countries="GB",
            search_in="title_content"
        )
        # print(get_response)
    except ApiException as e:
        print("Exception when calling AuthorsApi.get: %s\n" % e)
        pprint(e.body)
        if e.status == 422:
            pprint(e.body["detail"])
        pprint(e.headers)
        pprint(e.status)
        pprint(e.reason)
        pprint(e.round_trip_time)

    get_response.articles[0]

    news_articles = ''
    for article in get_response.articles[:10]:
      title   = article['title']
      content = article['content']
      print(title)
      print(article['score'])
      news_articles += remove_unusual_characters(title)
      news_articles += '\n'
      news_articles += remove_unusual_characters(content)
      news_articles += '------------------------------------'

    newscatcher_submission_prompt = """
        Beneath the dashed line below is the relevant news related to the topic of the legislation.

        Read through each example to gain context and how it can feed into the explanatory notes of the legislation document.

        Please generate a short paragraph summarising the background that these news articles have given you, and why the legislation might be necessary.

        Do not generate your explanatory notes yet. Await the results of the legislation search.
        ----------------------------------------------------------------------
        """ + news_articles

    return newscatcher_submission_prompt

def add_news_data(post_document_messages, system_prompt, newscatcher_submission_prompt, client = anthropic_client):
    messages = post_document_messages

    # Add user prompt
    messages.append({"role": "user", "content": newscatcher_submission_prompt})
    # print(messages)

    message = client.messages.create(
        model="claude-3-opus-20240229",
        max_tokens=4000,
        temperature=0.5,
        system=system_prompt,
        messages=messages
    )

    # Assuming 'message.content' returns a list of objects and each object has a 'text' attribute
    # Here, we consider the first object's text for simplicity
    if message.content:  # Check if content is not empty
        new_message_text = message.content[0].text  # Accessing the text attribute of the first content item

        # Append a new dictionary to the messages list with the role of "assistant" and the extracted text content
        messages.append({"role": "assistant", "content": new_message_text})

        # Print the content of the new message
        # print(new_message_text)
    else:
        print("No content received from the API")

    post_newscatcher_messages = messages

    return post_newscatcher_messages

def legislation_api_call(legislation_search_string, results_count):
    """
    Fetch the first two entry URLs from an Atom feed based on the search term.
    """
    url = f'https://www.legislation.gov.uk/search/data.feed?text={legislation_search_string}&results-count={results_count}'
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'xml')

    # print("Feed Title:", soup.feed.title.string)
    
    entries = []
    for entry in soup.find_all('entry', limit=results_count):  # Limit to the first two entries
        entry_data = {
            "Title": entry.title.string,
            "Link": entry.link['href'],
            "Updated": entry.updated.string,
            "Summary": entry.summary.string if entry.summary else "No summary available"
        }
        entries.append(entry_data)

    # Print values
    # for ind, entry in enumerate(entries):
    #     print(f"Legislation {ind + 1}:")
    #     for key, value in entry.items():
    #         print(f"{key}: {value}")
    #     print()  # Print a newline for better separation between entries

    legislation_str = ''
    for article in entries:
      title   = article['title']
      content = article['content']
      print(title)
      print(article['score'])
      legislation_str += remove_unusual_characters(title)
      legislation_str += '\n'
      legislation_str += remove_unusual_characters(content)
      legislation_str += '------------------------------------'

    legislation_submission_prompt = """
        Beneath the dashed line below is the relevant historic legislation related to the topic of the legislation provided by the user.

        Read through each example to gain context and how it can feed into the explanatory notes of the legislation document.

        Please generate a short paragraph summarising the background that these legislative articles have given you, and why the legislation might be necessary.

        Do not generate your explanatory notes yet.
        ----------------------------------------------------------------------
        """ + news_articles 

    return legislation_submission_prompt


def add_legislation_data(post_document_messages, system_prompt, newscatcher_submission_prompt, client = anthropic_client):
    messages = post_document_messages

    # Add user prompt
    messages.append({"role": "user", "content": newscatcher_submission_prompt})
    # print(messages)

    message = client.messages.create(
        model="claude-3-opus-20240229",
        max_tokens=4000,
        temperature=0.5,
        system=system_prompt,
        messages=messages
    )

    # Assuming 'message.content' returns a list of objects and each object has a 'text' attribute
    # Here, we consider the first object's text for simplicity
    if message.content:  # Check if content is not empty
        new_message_text = message.content[0].text  # Accessing the text attribute of the first content item

        # Append a new dictionary to the messages list with the role of "assistant" and the extracted text content
        messages.append({"role": "assistant", "content": new_message_text})

    else:
        print("No content received from the API")

    post_newscatcher_messages = messages

    return post_newscatcher_messages



def draft_policy_background(post_newscatcher_messages, system_prompt, client = anthropic_client):
    draft_policy_background_prompt = """
        Now that you have recieved all of the necessary information pertaining to the legislation document, and have the relevant news articles surrounding it,
        please write the accompanying explanatory note policy background for the submitted document.
        Keep the document in the format previously specified and using a similar layout to the 'Fraud Act 2006' example shown but make sure that you do not copy this document exactly.
        The explanatory notes should refer only to the subject mentioned in the user's submitted legislation document.

        Can you please give it in json format where:
        Each subheadline contains the numbered bullets as children.

        An example below:

        <example>

        <input>
        INTRODUCTION 1. These explanatory notes relate to the Skateboard Act 2024 which received Royal Assent on [date]. 2. They have been prepared by the Department for Digital, Culture, Media and Sport in order to assist the reader in understanding the Act. They do not form part of the Act and have not been endorsed by Parliament. These notes need to be read in conjunction with the Act. They are not, and are not meant to be, a comprehensive description of the Act. 3. So where a section or part of a section does not seem to require any explanation or comment, none is given.
        BACKGROUND 4. Skateboarding has experienced a significant rise in popularity in recent years, particularly among children and young people. The sport's inclusion in the Olympics and its addition as a GCSE physical education option in Wales reflect its growing mainstream appeal and recognition as a legitimate physical activity. However, the increase in skateboarding has also raised concerns about safety, responsible use of public spaces, and potential nuisance caused by irresponsible skateboarding. While many skateboarders use the activity as a positive outlet for fitness, creativity, and community engagement, there have been instances of dangerous stunts and skateboard-related disturbances. • The skateboarding community itself is evolving, becoming more diverse and inclusive. There is a need to ensure that skateboarding remains accessible to people of all backgrounds, ages, and abilities, while also fostering a culture of responsibility and respect for public spaces. Skateboarding infrastructure and facilities have not always kept pace with the sport's rapid growth. Many areas lack proper skateparks, or have parks that were designed without sufficient consultation with the skateboarding community. Funding for skateboarding facilities is also often limited. In light of these developments, the government has recognized the need for a balanced approach to skateboarding regulation. The Skateboard Act 2024 aims to support the sport's continued growth and its benefits to participants, while also addressing legitimate concerns around safety and public order.
        </input>

        <json>
        {
        "Introduction": [
            "bullet": "These explanatory notes relate to the Skateboard Act 2024 which received Royal Assent on [date].",
            "bullet": "They have been prepared by the Department for Digital, Culture, Media and Sport in order to assist the reader in understanding the Act. They do not form part of the Act and have not been endorsed by Parliament. These notes need to be read in conjunction with the Act. They are not, and are not meant to be, a comprehensive description of the Act.",
            "bullet": "So where a section or part of a section does not seem to require any explanation or comment, none is given.",
        ],
        "Background": [
            "bullet": "Skateboarding has experienced a significant rise in popularity in recent years, particularly among children and young people. The sport's inclusion in the Olympics and its addition as a GCSE physical education option in Wales reflect its growing mainstream appeal and recognition as a legitimate physical activity. However, the increase in skateboarding has also raised concerns about safety, responsible use of public spaces, and potential nuisance caused by irresponsible skateboarding. While many skateboarders use the activity as a positive outlet for fitness, creativity, and community engagement, there have been instances of dangerous stunts and skateboard-related disturbances. • The skateboarding community itself is evolving, becoming more diverse and inclusive. There is a need to ensure that skateboarding remains accessible to people of all backgrounds, ages, and abilities, while also fostering a culture of responsibility and respect for public spaces. Skateboarding infrastructure and facilities have not always kept pace with the sport's rapid growth. Many areas lack proper skateparks, or have parks that were designed without sufficient consultation with the skateboarding community. Funding for skateboarding facilities is also often limited. In light of these developments, the government has recognized the need for a balanced approach to skateboarding regulation. The Skateboard Act 2024 aims to support the sport's continued growth and its benefits to participants, while also addressing legitimate concerns around safety and public order."
        ]
        }
        </json>
        """

    messages = post_newscatcher_messages

    messages.append({"role": "user", "content": draft_policy_background_prompt})
    messages.append({"role":"assistant","content":"{"})

    message = client.messages.create(
        model="claude-3-opus-20240229",
        max_tokens=1000,
        temperature=0.5,
        system=system_prompt,
        messages=messages
    )

    # Assuming 'message.content' returns a list of objects and each object has a 'text' attribute
    # Here, we consider the first object's text for simplicity
    if message.content:  # Check if content is not empty
        new_message_text = message.content[0].text  # Accessing the text attribute of the first content item

        # Append a new dictionary to the messages list with the role of "assistant" and the extracted text content
        messages.append({"role": "assistant", "content": new_message_text})

        # Print the content of the new message
        policy_background = new_message_text
    else:
        print("No content received from the API")

    final_messages = messages

    return final_messages, policy_background


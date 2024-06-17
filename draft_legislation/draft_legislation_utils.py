import anthropic
import os 
from bs4 import BeautifulSoup
import requests
import ast
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import utils


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
read_keys()

# creating client with api key from .env file
anthropic_client = anthropic.Anthropic(
    api_key=os.environ.get('ANTHROPIC_API_KEY'))

#model = "claude-3-haiku-20240307"
# model = "claude-3-opus-20240229"
#model = "claude-3-opus-20240229"


def get_concept(scheme,model):

    system = """
Your task is to interpret a draft of a piece of regulatory legislation. 
You must return the most relevant concept that is most associated with the legislation itself.
This concept is key to the interpretation of the legislation. The 'concept' will most likely be an object (e.g. 'sunbed') or an action (e.g. 'smoking').
Return ONLY with the concept in the legislation that has different interpretations.

Here is an example of what you must provide. 

<example>
<draft>
A person who operates or uses a sunbed in a sunbed business in England must have a licence.
The local authority is to set the fee for a licence, which must be calculated so as to cover the expected costs of the licensing regime (and not to make a profit).
A licence for a sunbed may be granted subject to conditions, for example about the maximum exposure time, the provision of protective eyewear, or the display of health warning signs. A condition may be imposed only for the purposes of public health and safety.
The local authority may cancel a licence if the person to whom the licence has been granted fails to comply with the conditions of the licence or operates the sunbed business in an unsafe manner. There is a right of appeal to the county court against a cancellation of a licence.
</draft>

<concept>
Sunbed 
</concept>
</example>

Here is another example.

<example>
<draft>
Smoking in enclosed public spaces and workplaces in England is prohibited.
The local authority is responsible for enforcing the smoking ban.
Owners, managers, and persons in control of premises where smoking is prohibited must display "No Smoking" signs and take reasonable steps to ensure compliance with the ban.
A person who smokes in a prohibited area commits an offence. The offence is a summary offence, with a penalty of a fine not exceeding level 3 on the standard scale.
</draft>

<concept>
Smoking 
</concept>
</example>
"""

    prompt = f"""
<draft>
{scheme}
</draft>"""
    response = f"""
<concept>"""

    res = anthropic_client.messages.create(
        model=model,
        max_tokens=20,
        temperature=0.8,
        system=system,
        messages=[
            {"role": "user", "content": [{"type": "text", "text": prompt}]},
            {"role": "assistant", "content": [{"type": "text", "text": response}]},
        ],
    )
    res = res.content[0].text.split("</concept>")[0].replace("/n", "").strip()
    return res


def get_interpretation(concept,model):

    system = """
You are an expert legal interpreter.
Your task is to take a concept, often an object or action, and provide a number of potentially different interpretations. 
You must provide interpretations as a numbered list that contains 3-4 items only.
The interpretations must be concise, clear and wide-ranging, without being overly specific.

Here is an example of what you must provide. 

<example>
<draft>
Sunbed
</draft>

<interpretation>
(1) The following provisions apply for the interpretation of this Act.

(2) \"Sunbed\" means an electrically-powered device designed to produce tanning of the human skin by the emission of ultra-violet radiation.

(3) A \"sunbed business\" is a business that involves making one or more sunbeds available for use on premises that are occupied by, or are to any extent under the management or control of, the person who carries on the business; and those sunbeds are the sunbeds to which the business relates.
</interpretation>
</example>

Here is another example.

<example>
<concept>
Smoking
</concept>

<interpretation>
(1) The following provisions apply for the interpretation of this Act.

(2) \"Smoking\" the action or habit of inhaling and exhaling the smoke of tobacco by sucking on the end of a lit cigarette, cigar, pipe, etc.

(3) For the purposes of this Act, “smoking” includes being in possession of lit tobacco or any other lit substance in a form in which it could be smoked.

(4) \"The smoking ban\" refers to the prohibition of smoking in enclosed public spaces and workplaces in England.
</example>
"""

    prompt = f"""
<concept>
{concept}
</concept>"""
    response = f"""
<interpretation>

(1) The following provisions apply for the interpretation of this Act."""

    res = anthropic_client.messages.create(
        model=model,
        max_tokens=256,
        temperature=0.7,
        system=system,
        messages=[
            {"role": "user", "content": [{"type": "text", "text": prompt}]},
            {"role": "assistant", "content": [{"type": "text", "text": response}]},
        ],
    )
    res = res.content[0].text.split("</interpretation>")[0].replace("/n", "").strip()
    # add (1) The following provisions apply for the interpretation of this Act."""
    res = response + '/n/n' + res
    res = res.replace('<interpretation>','')
    return res, prompt,system


def get_structure(draft,model):

    system = """
You are an expert legal interpreter. You have been provided a draft of a piece of legislation, you must describe the structure.
You must provide a single list containing the heading of each section of the legislation.
Propose approximately 10 sections.
Do not include a section that is a summary, or introductory text.
Alongside the title there is a brief description associated with the title. 
Both the title and description are given as a list.
Never include a commencement, extent, or short title section.

Here is an example of what you must provide. 

<example>
<draft>
Smoking in enclosed public spaces and workplaces in England is prohibited.
The local authority is responsible for enforcing the smoking ban.
Owners, managers, and persons in control of premises where smoking is prohibited must display "No Smoking" signs and take reasonable steps to ensure compliance with the ban.
A person who smokes in a prohibited area commits an offence. The offence is a summary offence, with a penalty of a fine not exceeding level 3 on the standard scale.
</draft>

<structure>
[
    ["Main interpretative provisions",
    "Defines the main interpretative provisions of the Act"],

    ["Prohibition on smoking in enclosed public spaces and workplaces",
     "Describes the prohibition of smoking in enclosed public spaces and workplaces in England"],

    ["Exemptions for designated smoking rooms and specific premises",
        "Specifies any exemptions or designated smoking areas"],

    ["Display of no-smoking signs",
    "Outlines the requirements for owners, managers, and persons in control of premises where smoking is prohibited to display 'No Smoking' signs"],

    ["Offence of smoking in a prohibited place",
    "Defines the offence of smoking in a prohibited area and the associated penalties"],

    ["Offence of failing to prevent smoking in a prohibited place",
    "Describes the offence of failing to prevent smoking in a prohibited area and the associated penalties"],

    ["Enforcement by local authorities",
    "Outlines the responsibilities of local authorities in enforcing the smoking ban"],

    ["Powers of entry and inspection for authorised officers",
    "Specifies the powers of entry and inspection for authorised officers"],

    ["Obstruction etc. of authorised officers",
    "Describes the offence of obstructing or failing to cooperate with authorised officers"],

    ["Offences by bodies corporate",
    "Outlines the liability of bodies corporate for offences under the Act"],

    ["Fixed penalty notices",
    "Provides for the issuance of fixed penalty notices for certain offences"]

    ["Financial provisions",
    "Specifies any financial provisions related to the Act"]
]
</structure>

</example>

Here is another example.

<example>
<draft>
A person who operates or uses a sunbed in a sunbed business in England must have a licence.
The local authority is to set the fee for a licence, which must be calculated so as to cover the expected costs of the licensing regime (and not to make a profit).
A licence for a sunbed may be granted subject to conditions, for example about the maximum exposure time, the provision of protective eyewear, or the display of health warning signs. A condition may be imposed only for the purposes of public health and safety.
The local authority may cancel a licence if the person to whom the licence has been granted fails to comply with the conditions of the licence or operates the sunbed business in an unsafe manner. There is a right of appeal to the county court against a cancellation of a licence.
</draft>

<structure>
[
    ["Main interpretative provisions",
    "Defines the main interpretative provisions of the Act"],

    ["Duty to prevent sunbed use by children",
    "Prohibits the use of sunbeds by individuals under the age of 18 in sunbed businesses"],

    ["Exemption for medical treatment",
    "Provides an exemption for the use of sunbeds for medical treatment purposes"],

    ["Power to make further provision restricting use, sale or hire of sunbeds",
    "Grants the authority to make additional provisions restricting the use, sale, or hire of sunbeds"],

    ["Power to require information to be provided to sunbed users",
    "Authorises the requirement for information to be provided to sunbed users"],

    ["Protective eyewear",
    "Legislates for the provision of protective eyewear for sunbed users"],

    ["Enforcement by local authorities",
    "Outlines the responsibilities of local authorities in enforcing the licensing regime"],

    ["Obstruction etc. of authorised officers",
    "Describes the offence of obstructing or failing to cooperate with authorised officers"],

    ["Offences by bodies corporate",
    "Outlines the liability of bodies corporate for offences under the Act"],

    ["Financial provisions",
    "Specifies any financial provisions related to the Act"]
]
</structure>
</example>
"""

    prompt = f"""
<draft>
{draft}
</draft>"""
    response = f"""
<structure>

    [
    ["Main interpretative provisions",
    "Defines the main interpretative provisions of the Act"],"""

    res = anthropic_client.messages.create(
        model=model,
        max_tokens=512,
        temperature=0.7,
        system=system,
        messages=[
            {"role": "user", "content": [{"type": "text", "text": prompt}]},
            {"role": "assistant", "content": [{"type": "text", "text": response}]},
        ],
    )
    res = res.content[0].text.split("</structure>")[0]
    res = """
[
    ["Main interpretative provisions",
    "Defines the main interpretative provisions of the Act"],""" + res

    res = ast.literal_eval(res)
    return res,prompt,system


def draft_section_call(draft,section,explanation,all_sections,model):

    system = f"""
You are an expert legal interpreter. You have been provided a draft of a piece of legislation, and a section heading. 
You must provide a draft of the section that corresponds to the heading.
You must ensure that the content you provide is consistent with the original drafted legislation. 
You will also receive a brief description of the specific section to guide you in drafting the content. 

Subsection may be used but are not needed unless structurally required. 

Never provide concept interpretations within the section (e.g. for the purposes of this section..."Sunbed" means an electrically-powered ...)
All interpretations have been previously defined.

Here are all the sections and descriptions. Do not cover any content that is not immediately relevant to the section you are drafting.

<all-sections>
{all_sections}
</all-sections>

Here is some information about writing effective legislation structures:

<information>
Telling the story
Take readers by the hand and lead them through the story you have to tell. Imagine that you are trying to explain something orally to interested listeners. Where would you start? What will they want to know first?
It may help to give readers an overview of the whole story at the outset, so that they can understand each part in the light of the whole. Readers are more likely to understand something if they know why you are telling them.
Sometimes the table of contents can give a suitable overview. Or you could have an overview clause.
Of course, a finished Act will have many different readers with different interests (those who are subject to its provisions, professional advisers, the courts). And the readers of a Bill (as opposed to an Act) will be different again — Ministers, members of the two Houses of Parliament, as well as lobby groups and other interested parties. These competing interests need to be balanced and given due weight in what we write.

Find a logical order and structure
Finding a clear order in which to tell your story is fundamental. This goes for a story which is spread across a whole Bill or for a story contained in a single clause.
The material in your Bill should be set out in a logical order, so that later propositions build upon earlier ones.
Cross-references can prove hard work for the reader, so it is helpful to minimise their use. This can sometimes be done by re-ordering the material.
Similarly, find a Bill structure which shows how your provisions fit together. Let the divisions in your Bill reflect the divisions of thought.

Get to the point
Get to the point as quickly as you can. Ideally the opening subsection of a clause will contain the main proposition or at least give the reader some idea of what the clause is about. Don’t bury the main proposition away in the middle of the clause if you can possibly avoid it.
So if the clause produces a particular legal effect if conditions are met, it may be more helpful to state the effect before listing the conditions.

EXAMPLE

A notice must be given if… (several conditions)…
is probably easier to understand than—
If…(several conditions)… a notice must be given.

Keep propositions short
Clarity is helped by the use of short sentences. A long sentence may require the reader to keep too much in the mind. So on the whole it’s best to try to stick to one idea per sentence.
That said, a single complex proposition is sometimes best expressed in a single sentence, rather than as a series of short sentences in successive subsections which then have to be put back together again to make sense.

The medium is not the message
A Bill should not draw any more attention to its own structure and mechanics than it needs to. The reader is likely to be interested in how a Bill changes the law; drafting in a way that draws more attention to the structure and mechanics of the Bill itself than to its effect is likely to be unhelpful.
In particular, don’t create more artificial structure, such as Chapters and Parts, than you need to.

Tone
Tell your story in a moderate, level tone. Legislation should speak firmly but not shout.
While brevity may be good, brusqueness is not. Avoid excessive emphasis, which may be distracting (for example, unnecessary use of “But” at the beginning of a sentence).
</information>

Here are some examples

<example>
<description>
A person who operates or uses a sunbed in a sunbed business in England must have a licence.
The local authority is to set the fee for a licence, which must be calculated so as to cover the expected costs of the licensing regime (and not to make a profit).
A licence for a sunbed may be granted subject to conditions, for example about the maximum exposure time, the provision of protective eyewear, or the display of health warning signs. A condition may be imposed only for the purposes of public health and safety.
The local authority may cancel a licence if the person to whom the licence has been granted fails to comply with the conditions of the licence or operates the sunbed business in an unsafe manner. There is a right of appeal to the county court against a cancellation of a licence.
</description>

<section-title>
Duty to prevent sunbed use by children
</section-title>

<section-explanation>
Prohibits the use of sunbeds by individuals under the age of 18 in sunbed businesses
</section-explanation>

<section>
- Prohibit the use of sunbeds by individuals under the age of 18 in sunbed businesses
    - Make it the responsibility of the sunbed business operator to ensure compliance
    - Ban offering sunbed services to under-18s
    - Prevent under-18s from being present in restricted zones of the business, except when providing services for the business
- Define "relevant premises" where these rules apply:
    - Premises occupied, managed, or controlled by the sunbed business operator
    - Exclude domestic premises
- Establish "restricted zones":
    - Wholly or partly enclosed spaces reserved for sunbed users
    - Rooms containing sunbeds, even if not in an enclosed space
- Set penalties for non-compliance:
    - Offence committed by the sunbed business operator for failing to comply
    - Liable for a fine upon summary conviction
- Define Age limit for sunbed use
- Provide a defence for charged persons:
    - Must show they took all reasonable precautions and exercised due diligence to avoid committing the offence
- Allow for exemptions:
    - Medical treatment purposes (to be detailed in a separate section)
</section>
</example>


Here is another example.

<example>
<draft>
The Financial Conduct Authority (FCA) and the Prudential Regulation Authority (PRA) must issue a statement of policy regarding their exercise of regulatory functions.
The policy should outline the imposition and duration of temporary prohibitions relating to management functions, as well as the imposition and determination of financial penalties.
When determining penalties, the policy must require the regulator to consider relevant factors such as the contravention's impact, the person's responsibility, financial position, and cooperation level.
The FCA and PRA must publish the statement, provide a copy to the Treasury, and adhere to the policy when exercising their powers related to temporary prohibitions and financial penalties.
</draft>

<section-title>
Statement of Policy for Temporary Prohibitions and Financial Penalties by FCA and PRA
</section-title>

<section-explanation>
The FCA and PRA must issue a policy statement outlining their approach to imposing temporary prohibitions and financial penalties, considering relevant factors, and adhere to this policy when exercising these powers.
</section-explanation>

<section>
- The FCA and PRA must prepare and issue a statement of policy regarding their exercise of functions as appropriate regulator, including:
  - Imposing temporary prohibitions relating to management functions
  - Determining the period of such prohibitions
  - Imposing financial penalties
  - Determining the amount of financial penalties
- When determining the amount of a penalty, the policy must require the appropriate regulator to consider relevant circumstances, such as:
  - Impact, gravity, and duration of the contravention
  - The person's responsibility for the contravention
  - The person's financial position
  - Profit gained or loss avoided due to the contravention
  - Loss sustained by others due to the contravention
  - The person's level of cooperation with the regulator
  - Any previous contraventions by the person
- The FCA or PRA may alter or replace the issued statement and must issue the altered or replacement statement.
- The FCA or PRA must provide a copy of the statement to the Treasury without delay.
- The statement must be published by the FCA or PRA in a manner that brings it to the public's attention.
- The FCA or PRA may charge a reasonable fee for providing a copy of the statement.
- When exercising or deciding whether to exercise its power regarding temporary prohibitions or financial penalties, the appropriate regulator must consider the statement of policy that was in force at the time of the contravention.
</section>

</example>"""

    prompt = f"""
<draft>
{draft}
</draft>

<section-title>
{section}
</section-title>

<section-explanation>
{explanation}
</section-explanation>"""

    response = f"""
<section>"""

    res = anthropic_client.messages.create(
        model=model,
        max_tokens=512,
        temperature=0.7,
        system=system,
        messages=[
            {"role": "user", "content": [{"type": "text", "text": prompt}]},
            {"role": "assistant", "content": [{"type": "text", "text": response}]},
        ],
    )
    res = res.content[0].text.split("</section>")[0]
    return res, prompt, system

def finetune_section(proposed_act,section_title, section,all_sections,explanation,model):

    system = f"""
You are a legal expert. You have been provided a draft of a piece of legislation, and a section heading. 
You must edit, correct, and format this draft appropriately.
Within the draft of the piece of legislation, you may provide cross-links to other subsections within the legislation.
Importantly, the subsections refer to each other in a relevant and concise way and only when necessary.
You must also enumerate subsections like this (1), (2), (3), etc. and subsubsections with letters like this (a), (b), (c), etc.
At this stage you must use formal language as in the below examples.

Here is a description of the drafted Act as originally provided. The following section you will be given corresponds to content within this Act.
You must make sure that the content you provide is consistent with the original Act.

A section, subsection, or subsubsection should always have associated text. NEVER EVER USE THE WORD "SHALL".

Here are all the sections of the legislation. Do not cover any content that is not relevant to the section you are drafting.
Ensure that the content you provide does not overlap with other sections.

<all-sections>
{all_sections}
</all-sections>

Here is some information about writing effective syntax for writing legislation 

<information>
Sentence structure
Sentences should be simply and logically constructed. The classic structure is subject-verb-object. If possible, avoid inserting words between the subject and the main verb.

EXAMPLE
Instead of—
The Secretary of State may, if the required conditions are met, issue a licence to the applicant.
you could say—
The Secretary of State may issue a licence to the applicant if the required conditions are met.

Positive and negative
The positive is often easier to understand than the negative.

EXAMPLE

Speak after the tone
is easier to understand than—
Do not speak until you hear the tone
This is of course not a universal rule. A prohibition may be best expressed in the negative (“do not walk on the grass” as opposed to “walk on the path”).
Express quantities positively rather than negatively.

EXAMPLE
25% or more
rather than
not less than 25%

Avoid double negatives wherever it is not impossible to do so.

Active and passive
The active voice is generally understood more readily than the passive.

EXAMPLE
The Secretary of State must give a notice
rather than
A notice must be given by the Secretary of State
The passive may be appropriate if the agent is unimportant, universal or unknown.

EXAMPLE

If a notice is given to the Authority…
might be appropriate if the same rule applies whoever gave the notice.

Verbs and nouns
A verb is often easier to understand than a noun.

EXAMPLE
A person may apply
is crisper and more instantly intelligible than—
A person may make an application

“Shall”
Office policy is to avoid the use of the legislative “shall”.[footnote 1] There may of course be exceptions. One reason for using “shall” might be where the text is being inserted into an Act that already uses it.

VOCABULARY
Which words to choose?
Write in modern, standard English using vocabulary which reflects ordinary general usage. So avoid archaisms and other words or phrases which can give rise to difficulty. Equally, it is not our role to be in the vanguard of linguistic development.

Sir Ernest Gowers proposed three principles as to “how best to convey our meaning without ambiguity and without giving unnecessary trouble to our readers”.[footnote 2]
• use no more words than are necessary;
• use the most familiar words;
• use precise and concrete words rather than vague and abstract words.
These three principles are hard to beat as a starting-point.[footnote 3] They do of course overlap with and support each other.

Use no more words than necessary
This principle takes on additional force in legislative drafting for obvious reasons to do with avoiding confusion and ambiguity.
We should prefer the single word to what Gowers describes as the “roundabout phrase”. It is easy to slip into saying “for the purpose of” when very often we could just say “to”; or “in accordance with” when we could use “by” or “under”.

Use the most familiar words
Avoid words that are not found in standard modern writing in English. In the first place, avoid archaisms (for example, “here-” and “there-” words such as “herewith” or “thereby”).
The novel and modish can be as “far-fetched” and unfamiliar as the archaic. We should try not to use language that calls attention to itself.
We should also avoid jargon, whether legal jargon or policy jargon. It may of course sometimes be necessary to use technical legal expressions.
This principle, though, does not merely filter out archaisms, neologisms and jargon. There are degrees of familiarity. You may have two words neither of which is “far-fetched” or incomprehensible but one of which may be more familiar or everyday than the other. In that case, it is worth considering using it. For example, confer is a perfectly unobjectionable word, but this principle might suggest giving thought to the more familiar give. You might require particulars to be given, but if all you mean is information, why not say that?[footnote 4]
There is of course a caveat. Only use the more familiar word if it conveys the meaning equally well.

Use precise and concrete words
Drafters are used to drawing on words with a broad range of meanings such as “affect” or “in relation to”. These can be very useful, if a broad range of meaning is intended, as it often is. But if a more precise word can be used, it is more likely to get the actual intention across.
Text with a lot of opaque words may cause readers’ eyes to glaze over. While it is not our job to spice things up, we are failing our readers if we produce text that is impenetrable or unnecessarily turgid.
Here are some examples of potentially vague words. Sometimes their breadth of meaning is just what a drafter needs. But if in the context it is possible to be more precise, that may be more helpful to the reader.
• affect (limit, restrict)
• prescribe (specify, set out)
• provide for (specify, make, enable, authorise)
• make provision about (what exactly?)
• in relation to, in respect of (for, about)
• subject to (limited or restricted by)
• without prejudice (does not limit or restrict)
</information>


Here are some examples

<example>

<draft-act>
A person who operates or uses a sunbed in a sunbed business in England must have a licence.
The local authority is to set the fee for a licence, which must be calculated so as to cover the expected costs of the licensing regime (and not to make a profit).
A licence for a sunbed may be granted subject to conditions, for example about the maximum exposure time, the provision of protective eyewear, or the display of health warning signs. A condition may be imposed only for the purposes of public health and safety.
The local authority may cancel a licence if the person to whom the licence has been granted fails to comply with the conditions of the licence or operates the sunbed business in an unsafe manner. There is a right of appeal to the county court against a cancellation of a licence.
</draft-act>

<section-title>
Duty to prevent sunbed use by children
</section-title>

<section-explanation>
Prohibits the use of sunbeds by individuals under the age of 18 in sunbed businesses
</section-explanation>

<section>
- Prohibit the use of sunbeds by individuals under the age of 18 in sunbed businesses
    - Make it the responsibility of the sunbed business operator to ensure compliance
    - Ban offering sunbed services to under-18s
    - Prevent under-18s from being present in restricted zones of the business, except when providing services for the business
- Define "relevant premises" where these rules apply:
    - Premises occupied, managed, or controlled by the sunbed business operator
    - Exclude domestic premises
- Establish "restricted zones":
    - Wholly or partly enclosed spaces reserved for sunbed users
    - Rooms containing sunbeds, even if not in an enclosed space
- Set penalties for non-compliance:
    - Offence committed by the sunbed business operator for failing to comply
    - Liable for a fine upon summary conviction
- Provide a defence for charged persons:
    - Must show they took all reasonable precautions and exercised due diligence to avoid committing the offence
- Allow for exemptions:
    - Medical treatment purposes (to be detailed in a separate section)
</section>

<complete-section>
(1) A person who carries on a sunbed business (“P”) must secure—
    (a) that no person aged under 18 uses on relevant premises a sunbed to which the business relates;
    (b) that no offer is made by P or on P's behalf to make a sunbed to which the business relates available for use on relevant premises by a person aged under 18;
    (c) that no person aged under 18 is at any time present, otherwise than in the course of providing services to P for the purposes of the business, in a restricted zone.
(2) In this section “relevant premises” means premises which—
    (a) are occupied by P or are to any extent under P's management or control, and
    (b) are not domestic premises.
(3) Subsections (4) and (5) have effect for determining what is for the purposes of subsection (1)(c) a “restricted zone”.
(4) If a sunbed to which the business relates is in a wholly or partly enclosed space on relevant premises that is reserved for users of that sunbed, every part of that space is a restricted zone.
(5) If a sunbed to which the business relates is in a room on relevant premises, but not in a space falling within subsection (4), every part of that room is a restricted zone.
(6) If P fails to comply with subsection (1), P commits an offence and is liable on summary conviction to [F1a fine].
(7) It is a defence for a person (“D”) charged with an offence under this section to show that D took all reasonable precautions and exercised all due diligence to avoid committing it.
(8) This section is subject to section 3 (exemption for medical treatment).
</complete-section>
</example>


Here is another example.

<example>

<draft-act>
An act to provide for the temporary prohibition or restriction of traffic on roads; and for connected purposes.
Traffic authorities may temporarily restrict or prohibit the use of a road or part of a road by vehicles or pedestrians.
The local authority must consult with the relevant National Park authority before making an order that would affect a National Park.
Traffic authorities may temporarily restrict or prohibit road use by notice if necessary for works, litter clearing, or due to danger to the public or road.
Authorities must consider alternative routes for affected traffic when making an order or issuing a notice.
Provisions may be made by an order or notice, including restrictions on speed and access to premises.
Orders or notices must not prevent pedestrian access to premises on the road.
</draft-act>


<section-title>
Temporary prohibition or restriction on roads.
</section-title>

<section-explanation>
Allow traffic authorities to temporarily restrict or prohibit the use of a road or part of a road by vehicles or pedestrians.
</section-explanation>

<section>
- Allow traffic authorities to temporarily restrict or prohibit the use of a road or part of a road by vehicles or pedestrians through an order if:
    - Works are being or proposed to be executed on or near the road
    - There is a likelihood of danger to the public or serious damage to the road, not attributable to works
    - It is necessary to discharge the duty of litter clearing and cleaning under the Environmental Protection Act 1990
- Require traffic authorities to consult with the relevant National Park authority before making an order that would affect a National Park
- Permit traffic authorities to temporarily restrict or prohibit road use by notice if:
    - It is necessary or expedient for the execution of works or litter clearing and cleaning
    - It is necessary due to the likelihood of danger to the public or serious damage to the road, and the restriction or prohibition should come into force without delay
- Require authorities to consider alternative routes suitable for the affected traffic when making an order or issuing a notice
- Specify the provisions that may be made by an order or notice, including:
    - Provisions similar to those in section 2(1), (2), (3) or 4(1) of the Act
    - Provisions restricting the speed of vehicles
- Prohibit orders or notices that would prevent pedestrian access to premises situated on, adjacent to, or accessible only from the road
- Allow for provisions to be made regarding alternative roads, either by the initiating authority or with the consent of the traffic authority for the alternative road
- Permit orders or notices to suspend certain statutory provisions, with or without imposing restrictions or prohibitions
- Define "alternative road" in relation to a road subject to an order or notice
</section>

<complete-section>
(1) If the traffic authority for a road are satisfied that traffic on the road should be restricted or prohibited—
    (a) because works are being or are proposed to be executed on or near the road; or
    (b) because of the likelihood of danger to the public, or of serious damage to the road, which is not attributable to such works; or
    (c) for the purpose of enabling the duty imposed by section 89(1)(a) or (2) of the Environmental Protection Act 1990 (litter clearing and cleaning) to be discharged, the authority may by order restrict or prohibit temporarily the use of that road, or of any part of it, by vehicles, or vehicles of any class, or by pedestrians, to such extent and subject to such conditions or exceptions as they may consider necessary. [F2(1A)Before making an order under subsection (1) above, the authority shall consult the National Park authority for any National Park which would be affected by the order.]
(2) The traffic authority for a road may at any time by notice restrict or prohibit temporarily the use of the road, or of any part of it, by vehicles, or vehicles of any class, or by pedestrians, where it appears to them that it is—
    (a) necessary or expedient for the reason mentioned in paragraph (a) or the purpose mentioned in paragraph (c) of subsection (1) above; or
    (b) necessary for the reason mentioned in paragraph (b) of that subsection, that the restriction or prohibition should come into force without delay.
(3) When considering the making of an order or the issue of a notice under the foregoing provisions an authority shall have regard to the existence of alternative routes suitable for the traffic which will be affected by the order or notice.
(4) The provision that may be made by an order or notice under the foregoing provisions is—
    (a) any such provision as is mentioned in section 2(1), (2) or (3) or 4(1) of this Act; or
    (b) any provision restricting the speed of vehicles; but no such order or notice shall be made or issued with respect to any road which would have the effect of preventing at any time access for pedestrians to any premises situated on or adjacent to the road, or to any other premises accessible for pedestrians from, and only from, the road.
(5) Where any such order or notice is made or issued by an authority (in this subsection referred to as the “initiating authority”) any such provision as is mentioned in subsection (4) above may be made as respects any alternative road—
    (a) if that authority is the traffic authority for the alternative road, by an order made by the initiating authority or by that notice;
    (b) if the initiating authority is not the traffic authority for the alternative road, by an order made by the initiating authority with the consent of the traffic authority for the alternative road.
(6) Section 3(1) and (2) of this Act shall apply to the provisions that may be made under subsection (5) above as they apply to the provisions of a traffic regulation order.
(7) An order or notice made or issued under this section may—
    (a) suspend any statutory provision to which this subsection applies; or
    (b) for either of the reasons or for the purpose mentioned in subsection (1) above suspend any such provision without imposing any such restriction or prohibition as is mentioned in subsection (1) or (2) above.
(8) Subsection (7) above applies to—
    (a) any statutory provision of a description which could have been contained in an order or notice under this section;
    (b) an order under section 32(1)(b), 35, 45, 46 or 49 of this Act or any such order as is mentioned in paragraph 11(1) of Schedule 10 to this Act; and
    (c) an order under section 6 of this Act so far as it designates any parking places in Greater London.
(9) In this section “alternative road”, in relation to a road as respects which an order is made under subsection (1) or a notice is issued under subsection (2) above, means a road which—
    (a) provides an alternative route for traffic diverted from the first-mentioned road or from any other alternative road; or
    (b) is capable of providing such an alternative route apart from any statutory provision authorised by subsection (7) above to be suspended by an order made or notice issued by virtue of subsection (5) above.]
</complete-section>

</example>"""

    prompt = f"""

<draft-act>
{proposed_act}
</draft-act>

<section-title>
{section_title}
</section-title>

<section-explanation>
{explanation}
</section-explanation>

<section>
{section}
</section>"""

    response = f"""
<complete-section>"""

    res = anthropic_client.messages.create(
        model=model,
        max_tokens=512,
        temperature=0.7,
        system=system,
        messages=[
            {"role": "user", "content": [{"type": "text", "text": prompt}]},
            {"role": "assistant", "content": [{"type": "text", "text": response}]},
        ],
    )
    res = res.content[0].text.split("</complete-section>")[0]
    return res, prompt, system


def proofread_section(headers,section,model):

    system = """
You are a legal expert. You have been provided a draft of a piece of legislation, and a section heading. 
You must edit, correct, and format this appropriately, ensuring that links to sections and subsections are consistent across the legislation.
You must ensure that the numbering of subsections and subsubsections is correct.

Referring to other subsections when appropriate is always advised, you will receive information about the section names and numbers to guide the referencing. 

You must return valid JSON. Anything in quotes must be backslashed to ensure JSON is valid. I.e. \"Sunbed\".

Do not include 'Section X' in the "title" field, only the title of the section.

A section, subsection, or subsubsection should always have associated text, it cannot be empty.

All text must only be contained within a respective subsection or subsubsection. For example, text that applies to multiple subsections should be repeated for each subsection as opposed to presented singularly after the subsections.


<example-output>
    {
      "title": "Main interpretative provisions",
      "content": [
        {
          "subsection": "(1)",
          "text": "The following provisions apply for the interpretation of this Act."
        },
        {
          "subsection": "(2)",
          "text": " \"Sunbed\" means an electrically-powered device designed to produce tanning of the human skin by the emission of ultra-violet radiation.
        },
        {
          "subsection": "(3)",
          "text": "A \"sunbed business\" is a business that involves making one or more sunbeds available for use on premises that are occupied by, or are to any extent under the management or control of, the person who carries on the business; and those sunbeds are the sunbeds to which the business relates."
        }
      ]
    }
</example-output>

Here is an example output that deals with subsubsections appropriately 

<example-output>
{
    "title": "Powers of entry and inspection for authorised officers",
    "content": [
        {
            "subsection": "(1)",
            "text": "An authorised officer of a local authority may, on producing (if so required) evidence of their authority, exercise the following powers at all reasonable times for the purpose of enforcing the Act\u2014",
            "subsubsections": [
                {
                    "subsubsection": "(a)",
                    "text": "power to enter any premises (other than premises used wholly or mainly as a private dwelling) which the officer has reason to believe it is necessary to enter;"
                }
            ]
        }
    }
</example-output>


"""
    if headers:
        prompt = f"""
    <section-headers>
    {headers}
    </section-headers>"""
    else:
        prompt = ''

    prompt += f"""
{section}"""

    response = """
{"""

    temp = 0.7
    while True:
        try:
            res = anthropic_client.messages.create(
                model=model,
                max_tokens=4096,
                temperature=temp,
                system=system,
                messages=[
                    {"role": "user", "content": [{"type": "text", "text": prompt}]},
                    {"role": "assistant", "content": [{"type": "text", "text": response}]},
                ],
            )
            res = '{'+res.content[0].text
            res = ast.literal_eval(res)
            break
        except:
            print('Trying again...')
            print(res)
            temp = 0.9
            model = "claude-3-opus-20240229"
            continue

    return res, prompt, system



def repeat_offender(legislation,model):

    system = """
Your task is to take a piece of legislation and return it without any repeated content.
The format must be exactly the same as the original legislation, i.e. JSON, with the same fields
You must also fix references that are broken or incorrect (i.e. a reference to a section that does not exist, or section [X]).
"""

    prompt = f"""
{legislation}"""
    response = """{"""

    res = anthropic_client.messages.create(
        model=model,
        max_tokens=4096,
        temperature=0.8,
        system=system,
        messages=[
            {"role": "user", "content": [{"type": "text", "text": prompt}]},
            {"role": "assistant", "content": [{"type": "text", "text": response}]},
        ],
    )
    res = '{'+res.content[0].text
    res = ast.literal_eval(res)
    return res




def create_document(legislation_json,flag):

    data = legislation_json
    name = data['metadata']['title']
    # cut off last 13 chars
    creation_time = data['metadata']['modified'][:-13]

    # Create a new PDF document
    pdf_file = f"data/{data['metadata']['title']}/{flag}_act.pdf"

    doc = SimpleDocTemplate(pdf_file, pagesize=letter)

    # Get the default styles
    styles = getSampleStyleSheet()

    # Define custom styles
    # centered title
    # bold
    title_style = ParagraphStyle(name='Title', fontSize=20, leading=24, spaceAfter=12, alignment=1)
    content_title_style = ParagraphStyle(name='ContentTitle', fontSize=16, leading=20, spaceAfter=6, alignment=1)
    section_style = ParagraphStyle(name='Section', fontSize=16, leading=18, spaceBefore=12, spaceAfter=6)
    subsection_style = ParagraphStyle(name='Subsection', fontSize=12, leading=16, leftIndent=24, spaceAfter=6)
    subsubsection_style = ParagraphStyle(name='SubSubsection', fontSize=10, leading=14, leftIndent=48, spaceAfter=3)
    # smaller linespace for contents
    contents_style = ParagraphStyle(name='Contents', fontSize=14, leading=18, spaceAfter=6)

    # add title page
    elements = []

    header_style = ParagraphStyle(name='Header', fontSize=8, leading=12, alignment=1, fontname='Arial')
    elements.append(Paragraph(f"Modified - {creation_time}, NOT FINAL - CREATED USING GENERATIVE AI.", header_style))
    elements.append(Spacer(1, 0.25 * inch))
    elements.append(get_image('data/logo.png', width=1.5*inch))
    elements.append(Spacer(1, 0.25 * inch))

    elements.append(Paragraph('<b>'+name+'</b>', title_style))
    elements.append(Spacer(1, 0.4 * inch))

    section_numbers = [int(d['name'].split('.')[0].split('Section ')[-1]) for d in data['sections']]
    # sort data['sections'] by section number
    data['sections'] = [x for _, x in sorted(zip(section_numbers,data['sections']))]
    # add contents
    elements.append(Paragraph('<b>'+'Contents'+'</b>', content_title_style))
    elements.append(Spacer(1, 0.25 * inch))
    for section in data['sections']:
        elements.append(Paragraph('<b>'+section['name']+'</b>' + ' ' + section['title'], contents_style))
        #elements.append(Spacer(1, 0.25 * inch))

    elements.append(Spacer(1, 0.5 * inch))

    # Iterate over the sections in the JSON data
    for section in data['sections']:
        # Add the section title
        elements.append(Paragraph('<b>'+section['name'] + ' ' + section['title']+'</b>', section_style))
        
        # Iterate over the content in each section
        for content in section['content']:
            # Add the subsection
            try:
                elements.append(Paragraph(content['subsection'] + ' ' + content['text'], subsection_style))
            except:
                elements.append(Paragraph(content['subsection'], subsection_style))
            
            # Check if there are sub-subsections
            if 'subsubsections' in content:
                for subsubsection in content['subsubsections']:
                    # Add the sub-subsection
                    try:
                        elements.append(Paragraph(subsubsection['subsubsection'] + ' ' + subsubsection['text'], subsubsection_style))
                    except:
                        elements.append(Paragraph(subsubsection['subsubsection'], subsubsection_style))

        # Add a spacer between sections
        elements.append(Spacer(1, 0.25 * inch))

    # Build the PDF document
    doc.build(elements)


def create_draft_document(draf_json,metadata,prompt,context):
    '''
   [
    [
        "Main interpretative provisions",
        "Defines the main interpretative provisions of the Act"
    ],
    [
        "Licensing requirement for skateboard possession and use",
        "Establishes the requirement for a licence to possess or use a skateboard in England"
    ],
    [
        "Granting of licences by local authorities",
        "Specifies that licences are to be granted by local authorities"
    ],...]
    '''
    
    doc = SimpleDocTemplate(f"data/{metadata['title']}/structure.pdf", pagesize=letter)
    styles = getSampleStyleSheet()
    elements = []
    # add header with UTC and metadata at beginning
    creation_time = metadata['modified'][:-13]
    name = metadata['title']
    header_style = ParagraphStyle(name='Header', fontSize=10, leading=12, alignment=1)
    elements.append(Paragraph(f"Modified - {creation_time}, NOT FINAL - CREATED USING GENERATIVE AI.", header_style))
    elements.append(Spacer(1, 0.25 * inch))
    title_style = ParagraphStyle(name='Title', fontSize=20, leading=24, spaceAfter=12, alignment=1)

    # insert image
    elements.append(get_image('data/logo.png', width=1.5*inch))
    elements.append(Spacer(1, 0.25 * inch))

    elements.append(Paragraph('<b>'+f"Draft Legislation: {name}"+'</b>', title_style))
    elements.append(Spacer(1, 0.4 * inch))

    for section in draf_json:
        elements.append(Paragraph('<b>'+section[0]+'</b>', styles['Heading2']))
        elements.append(Paragraph(section[1], styles['Normal']))
        elements.append(Spacer(1, 0.25 * inch))

    # add appendix with prompt and context in computery writing 
    elements.append(Paragraph('<b>'+'Appendix'+'</b>', styles['Heading1']))

    elements.append(Paragraph('<b>'+'Context'+'</b>', styles['Heading2']))
    elements.append(Paragraph(context, styles['Normal']))
    elements.append(Spacer(1, 0.25 * inch))
    elements.append(Paragraph('<b>'+'Prompt'+'</b>', styles['Heading2']))
    elements.append(Paragraph(prompt, styles['Normal']))
    elements.append(Spacer(1, 0.25 * inch))
    
    doc.build(elements)

import datetime

def create_intermediary_document(titles,texts,prompts,contexts,path,act,type):
    '''
   [
    [
        "Main interpretative provisions",
        "Defines the main interpretative provisions of the Act"
    ],
    [
        "Licensing requirement for skateboard possession and use",
        "Establishes the requirement for a licence to possess or use a skateboard in England"
    ],
    [
        "Granting of licences by local authorities",
        "Specifies that licences are to be granted by local authorities"
    ],...]
    '''
    
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

    elements.append(Paragraph('<b>'+f"{type} Legislation: {act}"+'</b>', title_style))
    elements.append(Spacer(1, 0.4 * inch))

    for i in range(len(titles)):
        # add the title of section, the text, the context and prompt

        try:
            elements.append(Paragraph('<b>'+titles[i]+'</b>', styles['Heading1']))
        except:
            pass

        try:
            elements.append(Paragraph(texts[i], styles['Normal']))
        except:
            pass
        try:
            if prompts[i] is not None:
                elements.append(Spacer(1, 0.25 * inch))
                elements.append(Paragraph('<b>'+'Prompt'+'</b>', styles['Heading2']))
                elements.append(Paragraph(prompts[i], styles['Normal']))
                elements.append(Spacer(1, 0.25 * inch))
        except:
            pass

    # add appendix 
    elements.append(Paragraph('<b>'+'Appendix'+'</b>', styles['Heading1']))
    elements.append(Paragraph('<b>'+'Context'+'</b>', styles['Heading2']))
    i = 1
    while True:
        if i == len(contexts):
            break
        try:
            elements.append(Paragraph(contexts[i], styles['Normal']))
            break 
        except:
            i += 1

    doc.build(elements)



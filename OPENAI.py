import re
from loguru import logger
from openai import OpenAI
import json
from dotenv import load_dotenv
import os
from azure.identity import InteractiveBrowserCredential, get_bearer_token_provider
from openai import AzureOpenAI
load_dotenv()

RISK_TAXONOMY = {
    "Strategic Risk": {
        "Strategic priorities": "Risks that strategic priorities may not be aligned to the Bank's mission or risk of becoming irrelevant by not adapting to evolving demand.",
        "Governance and policy framework": "Risk that the Bank's effectiveness and efficiency are compromised, or opportunities are missed due to inadequate corporate or operational structure, inadequate policies and procedures, or roles and responsibilities.",
        "Strategic resources": "Risk arising from not having the adequate administrative and capital budget, human capital resources and information technology to implement the institutional strategy or that these are not aligned to the Bank's mission and strategic priorities.",
        "Shareholder and donor relationships": "Risk that relationship with shareholders or donors becomes ineffective, deteriorates, or becomes difficult for the Bank to manage."
    },
    "Financial Risk":{
        "Capital adequacy": "Risk that the Bank's existing capital base is not adequate to absorb market, credit, and operational risk related shocks or to meet borrower's demand for loans.",
        "Credit": "Potential loss that could result from the default of borrowers (loan portfolio credit risk or country credit risk) or from the default/ downgrade of investment or swap counterparties (commercial credit).",
        "Market": "Risk that changes in market rates (e.g., interest rates, credit spread, stock market values, or exchange rates) result in a loss or opportunity cost that affects the Bank's income or equity.",
        "Liquidity and funding": "Risk that the Bank is unable to fund its portfolio of assets at appropriate maturities and rates or unable to liquidate positions in a timely manner at reasonable rates."
    },
    "Corporate Operational Risk":{
        "Internal fraud and professional conduct": "Risks originated by Bank staff, complementary workforce, contractors and/or Directors in breach of the applicable ethics codes or other applicable Bank policies, including prohibited practices, omissions, or misrepresentations, which knowingly or recklessly mislead, or attempt to mislead.",
        "Information security breaches": "Risks arising from actors attempting to breach information systems or malicious or fortuitous behavior of internal users leading to security breaches of information systems.",
        "Employment practices and workplace safety": "Risks arising from acts inconsistent with employment, health or safety laws or agreements. ",
        "Business practices, product failures, and obligations": "Risks arising from an unintentional or negligent failure to meet an institutional obligation to specific IDB clients (borrower, investors & others) including product suitability or from the nature or design of a product.",
        "Damage to the Bank's physical assets and human wellbeing": "Risks arising from loss or damage to the Bank's physical assets or human wellbeing from natural disaster or other events (e.g., terrorism, civil unrest).",
        "Business disruption, system and data management failures": "Risks arising from system failures, inadequate IT infrastructure or disruption of business. ",
        "Transaction processing errors": "Risks arising from unintentional failed human transaction processing or inadequate process management, including failures from trade counterparties and vendors."
    },
    "Project Operational Risk":{
        "Ineffective project management, supervision, and portfolio management": "Risks arising from failures to adequately design, execute, close (project management) and/or supervise IDB financed operations; as well as to manage them as part of the Bank portfolio.",
        "Breach of obligations in IDB financed operations": "Risks arising from thirds parties’ failure to meet integrity or environmental and social requirements during the preparation and execution of an IDB-financed operation (including non-compliance with applicable IDB policies and regulations)."
    }
}

ILLUSTRATIVE_RISKS = {
    "Strategic Risk - Strategic priorities" : 
        {"Bank-wide strategic priorities": """
- Mission, values, goals, and priorities not relevant to the countries and the region.  
- Inflexible/outdated institutional strategy leading to missed opportunities for the Bank to have a greater impact. 
- Insufficient degree of implementation of the institutional strategy. 
- Country development outcomes identified in the Country Strategy are not aligned with the objectives set in the National Development Plan, and/or with the Bank’s institutional priorities, and/or Sector Framework Documents. 
- Country programming document is not consistent with the priorities defined in the Country Strategy. 
- Departmental business plans not aligned with institutional strategy.  
- Operations or IDB products and services disconnected from business plans and institutional strategy. 
- Bank does not achieve its strategic priorities. 
- Major events such as negative trending macroeconomic conditions, climate change events, pandemics, war, etc. impacting the ability to meet priorities, or rendering strategies obsolete. 
- Bank fails to meet borrowers’ needs and demands and becomes less relevant to the region.""", 
        "Innovation": """
- Inability to adapt to borrowers’ evolving needs and challenges. 
- Limited comparative advantage to other development players or non-traditional sources of funding in the region. 
- Inability to raise awareness among clients about opportunities and challenges of emerging technologies. 
- Inability to provide innovative solutions, or leverage new approaches and technologies in new or existing business areas to enhance efficiency and/or effectiveness."""},
    "Strategic Risk - Governance and policy framework" : {
        "Organizational structure": """
- Organizational structure not supporting the effective deployment of the institutional strategy.  
- Organizational structure inconsistent with roles and responsibilities or vice-versa. 
- Organizational chart does not reflect the approved organizational structure.""",
        "Policies & procedures": """
- Policies and procedures not aligned with strategic framework. 
- Failure to update policies and procedures in a timely manner or to clarify conflicting policies. 
- Policies and procedures not effective or efficient to achieve Bank objectives. 
- Potential deterioration in the Bank’s business profile, (governance policy framework as defined by rating agencies) leading to rating downgrade.  
- Policies and procedures not aligned with sound international practices affecting the Bank’s reputation and/or its work. """,
        "Roles & responsibilities ": """
- Inadequate or untimely information for decision making, due to lack of or unclear roles and responsibilities. 
- Unclear definition of roles and responsibilities lead to inefficiencies and/or duplication of work. """,
        "Culture risk": """
- Organizational culture prevents the achievement of its objectives."""
    },
    "Strategic Risk - Strategic resources" : {
        "Administrative and capital budget": """
- Disconnect between institutional priorities and allocation of budget resources. 
- Inability to deploy resources as needed.""",
        "People strategy": """
- Workforce management approach, which could impede an effective response to business needs. 
- Inadequate leadership and employee development programs to develop critical competencies. 
- Inability to attract, acquire, or retain the necessary human talent due to an ineffective employee value proposition. 
- Mismatch between the Bank’s needs and human capital skills and availability. 
- Mismatch between incentive structure to staff and institutional strategic priorities. 
- Insufficient rewards required to motivate and recognize staff performance and contributions.""",
        "Digital and information technology strategies": """
- Limitation in supporting geographically dispersed workforce through IT. 
- Limitations in supporting the institutional strategy, Bank-wide initiatives, and business functions through IT. 
- Business functions not supported through IT. 
- Mismatch between immediate business needs and lagging IT strategy.
- Limited or lack of adoption of emerging technologies and digital transformation """,
        },
    "Strategic Risk - Shareholder and donor relationships" : {
        "Shareholder relationship": """
- Bank seen as unresponsive or misaligned to shareholders’ expectations or strategy priorities,  
- Inability to retain or attract new member countries. 
- Bank seen as unresponsive, too responsive, or misaligned, to mandates of global financial governance fora (G20, UN, etc.). """,
        "Partners / Donors relationship": """
- Bank seen as unresponsive or misaligned to donor expectations or to commitments assumed by the Bank. 
- Inability to retain or attract new public and private partners. 
- Partnerships presenting integrity risks and/or impacting the Bank’s reputation.
- Project or activity not answering to the donors’ needs/expectations.  
- Inability to make commitments with partners on allocation of funding for co-financing grant activities.  
- Partnerships presenting risks when customized co-financing/ framework agreements require the implementation of a set of rules and procedures that differ from the Bank’s existing policies."""
    },
    "Financial Risk - Capital adequacy" : {
        "Capital adequacy": """
- Bank downgraded by one or more rating agencies, resulting in higher Bank borrowing costs, less reliable capital market access, lower lending capacity and/or higher loan charges. 
- Insufficient capital to cover losses in extreme situations leading to a call on the Bank’s Callable Capital"""
    },
    "Financial Risk - Credit" : {
        "Borrowers": """
- Deterioration in the overall quality of the Bank’s loan and guarantee portfolio. Including the impact of potential non-accruals in the Bank’s Sovereign Guaranteed (SG) portfolio. 
- Default under a Non-Sovereign Guaranteed (NSG) loan or guarantee that may result in a financial loss to the Bank.  
- Deterioration of the credit quality of lending portfolio and of the creditworthiness of the Bank’s borrowers may result in larger capital requirements and /or a reduction of the lending envelope.""",
        "Issuers and counterparties": """
- Issuers and counterparties failing to fulfill contractual obligations that result in deterioration in credit quality and potential financial loss. 
- Default or deterioration in credit rating or creditworthiness of an issuer of a security held by the Bank in its investment portfolio that may result in a financial loss to the Bank. 
- Default or deterioration of credit rating or creditworthiness of derivatives counterparties leading to increased credit and counterparty exposure, which may result in the Bank needing to replace counterparty hedges at a cost or remaining exposed in case no replacement is found."""
    },
    "Financial Risk - Market" : {
        "Treasury": """
- Changes in interest rates and swap and credit spreads may cause immediate mark-to-market losses in the investment portfolio. 
- Interest rates on Bank investment assets reset faster or slower than liabilities. 
- Investment securities are “called” or prepaid and re-invested at less favorable rates. 
- Changing interest rate relationships across maturities of interest rate curves. 
- Increase in funding spreads causes deterioration in the net spread earned on liquid assets. 
- Changes in other market risk factors such as spreads, and basis reduce income earned on investments.""",
        "Balance Sheet": """
- Low interest rate environment reduces income earned on equity-funded assets. 
- Rapidly increasing interest rates create opportunity losses on fixed-rate loans/ investments and duration swaps. 
- Interest rates on Bank loan assets reset faster or slower than liabilities. 
- Increase in funding spreads causes deterioration in the net spread of loans with fixed cost base. 
- Loans are prepaid and re-invested at less favorable rates. 
- Values of non-USD equity adversely impacted by currency movements. 
- Retirement plans’ funded status and/or expense is adversely affected by interest rate increases and/or investment return shortfalls."""
    },
    "Financial Risk - Liquidity and funding" : {
        "Liquidity and funding": """
- Bank is unable to borrow at reasonable rates. 
- Liquid assets are not available to meet IDB’s financial commitments. 
- Liquid assets not available to meet pension obligations."""
    },
    "Corporate Operational Risk - Internal fraud and professional conduct": {
        "Unauthorized activity": """
- Execution of unauthorized transactions (intentional). 
- Transaction executed and not reported (intentional). 
- Misclassification of transaction or financial position (intentional).""",
        "Prohibited practices (fraud, corruption, collusion, coercion, obstruction, misappropriation) and theft in the workplace": """
- Forgery, theft, embezzlement, robbery, extortion. 
- Financial statement fraud. - Misappropriation of Bank assets. 
- Malicious destruction of Bank assets. 
- Bribes/kickbacks. 
- Insider trading.""",
        "Other non-compliance with the Code of Ethics and Professional Conduct of the IDB, and ineffective labor relations": """
- Personal and/or financial conflict of interest. - Non-compliance with Bank’s internal policies. 
- Employee misconduct. 
- Breaches of confidentiality (intentional) including inappropriate use or transmission of proprietary or confidential information. 
- Public misrepresentation or misinformation regarding the Bank   
- Use of personal social media for unauthorized or improper communication.  
- Improper use of Bank communication tools."""},
    "Corporate Operational Risk - Information security breaches" : {
        "External user behavior leading to information security breaches": """
- The risk that vulnerabilities in networks, computers, or programs, flowing from or enabled by connections to third parties can be exploited.  
- Information lost, not available or tampered due to inadequate security measures by Cloud Service Provider (CSP).  
- Systems hacking, malicious intrusions and/or attack on Bank IT infrastructure affecting availability, integrity, or confidentiality of information.  
- Unauthorized system access or change to Bank data. Theft or compromise of Bank confidential information or Personal Identifiable Information (PII).  
- Website is defaced or attacked.""",
        "Internal user behavior leading to information security breaches": """
- Unauthorized internal system access or change to Bank data. 
- Theft or compromise of Bank confidential information or Personal Identifiable Information (PII) by internal user.  
- Unauthorized access to modify and/or alter financial transactions, including the possible alteration of the destination of the funds.  
- Lack of diligence in the application of security controls, especially those related to the adequate segregation of duties and authentication processes. """
    },
    "Corporate Operational Risk - Employment practices and workplace safety" : {
        "Staff and complementary workforce management, including the execution of the People Strategy": """
- Risks related to compensation, benefit, termination.  
- Risks related to the recruitment and retention, including loss of key personnel.  
- Misalignment of responsibilities to employee capabilities and obsolete employee skill set  
- Inadequate people managers to manage workplace conflict effectively. 
- Inadequate dissemination and communication of HR programs and Staff Rules. 
- Inconsistent application of Staff Rules and Bank policies. 
- Employee disengagement.""",
        "Employee health and safety": """
- Man-made internal sources of harm to people including workplace incidents. 
- General liabilities (slip and fall, etc.). - Workplaces not meeting accessibility requirements.""",
        "Diversity, equity, and inclusion": """
- Discrimination of all types (including in recruiting and hiring decisions, advancements and other opportunities) 
- Homogenous workforce"""
    },
    "Corporate Operational Risk - Business practices, product failures, and obligations" : {
        "Bank product, model risk or instrument flaws": """
- Model error or misuse   - Disputes over performance of client advisory activities. 
- Actuarial assumptions for retirement plans and postretirement funds may be wrong or inaccurate (actuarial risk).""",
        "Money Laundering and Financing of Terrorism (ML/FT) in corporate activities": """
- Failure to adequately mitigate institutional exposure to ML/FT  
- Establishing financial relationships with sanctioned entities within Bank activities.""",
        "Corporate fiduciary risks": """
- Fiduciary breaches / guideline violations. 
- Bank contractors and suppliers engage in prohibited practices or pose integrity risk. 
- Suitability / disclosure issues.  
- Breach of client privacy and misuse of confidential information. 
- Contractual and other relationships entered by the Bank fail to provide for the enforcement of the Bank’s rights or to adequately define the obligations of the counterparties. 
- Bank fails to comply with legal agreements and contracts. 
- Bank’s immunities may not be upheld, or the Bank may be forced to waive immunity."""
    },
    "Corporate Operational Risk - Damage to the Bank's physical assets and human wellbeing" : {
        "Damage to the Bank's physical assets": """
- Loss of the Bank’s physical assets due to natural disasters or other perils that would render the facilities inaccessible, non-functional, or unsafe. 
- Loss of the Bank’s physical assets due to external parties such as terrorism, and vandalism.""",
        "Damage to human wellbeing from external sources": """
- Human losses due to natural disasters (hurricane, earthquake, etc.), pandemic events, or other external sources of harm to people including warfare, terrorism, vandalism, kidnapping, etc.  
- Targeted criminal acts against Bank employees and executives."""
    },
    "Corporate Operational Risk - Business disruption, system and data management failures" : {
        "Technology infrastructure, equipment, software, and applications": """
- Hardware failures or hardware not adequate to meet the Bank’s needs. 
- Obsolete or unsupported software. - Ghost technology i.e., use of unknown/unapproved technology. 
- Software failures or software not meeting business needs. 
- Coding and program errors. 
- End-user computer failures. 
- Network and telecommunications failures. 
- Systemic failure. 
- Technology third-party vendor outages. 
- Utility outage / disruptions. 
- Denial of access to premises. 
- Inadequate governance of new and innovative technology.""",
    "IT data storage, retrieval, records management, and data privacy": """
- Inaccurate data classification and management.  
- Unsecured data / inadequate data protection. 
- Information not available or retrievable when needed. 
- Improper data retention i.e., early, or untimely destruction of records.  
- Compromised data integrity: outdated, inaccurate, or incomplete information. 
- Undefined data: amassing big data without defining and/or executing a strategy to utilize it effectively, thereby leading to unorganized or siloed data, information overload or outdated analytics. 
- License copyright infringement.  
- Destruction of information by natural disasters or other causes. 
- Lack of access to public information due to systems failure.
"""
    },
    "Corporate Operational Risk - Transaction processing errors" : {
        "Transaction capture, execution, and maintenance": """
- Miscommunication. 
- Data entry, maintenance or loading error. 
- Accounting error. 
- Reference data errors (exchange rates, market data, etc.)   
- Missed deadline or responsibility. 
- Failure to disclose to the public or classify information in content management system. 
- Payments due are not executed timely. 
- Funding or investment transactions fail to settle properly. 
- Collateral management failure.
- Other task underperformance. 
- Underperformance by other counterparties (i.e. executing agencies, securities custodians). 
- Customized co-financing/ frameworks that require the application of specific rules are not executed according to agreement.""",
        "Client intake and documentation": """
- Legal documents missing / incomplete. 
- Client permissions missing or undocumented. 
- Inadequate Customer / Client Account Management. 
- Payments to third parties that do not meet the AML/CFT standards.""",
        "Monitoring and reporting": """
- Untimely or inability to meet pre-committed reporting. 
- Inaccurate externally published report e.g., Information Statement, financial statements, disclosures, sustainability report, or other.""",
        "Vendors & suppliers": """
- Risk arising from third party relationships. 
- Inability of vendor/supplier to meet SLA.  
- Supply chain risk – inability of supplier to perform due to dependency on other vendors. 
- Inability to replace critical vendor. 
- Vendor disputes. 
- Missing contracts. 
- Vendor data security failure. 
- Vendor abuse of Bank resources and data. 
- Relationship with a vendor on a recognized sanctions list. 
- Direct payments on behalf of countries to third-parties on a sanctioned list. 
- Vendor action attracting negative media attention that reflects on the Bank.""",
        "Other counterparties": """
- Underperformance by other counterparties."""
    },
    "Project Operational Risk - Ineffective project management, supervision, and portfolio management": {
        "Project design": """
- Technical design issues such as faulty vertical logic, unrealistic targets, and unmeasurable indicators, difficult-to-meet technical quality requirements. 
- Poor project planning e.g., incorrect estimation of project duration and/or cost, failure to identify activity dependencies. 
- Inadequate design of project governance including poorly designed internal controls, too many actors involved, inadequate delivery arrangements, lack of effective communication mechanisms. 
- Obsolete design including climate transition risks. 
- Other sustainability issues including untenable technology, lack of consumer/investor demand, lack of acknowledgements of market trends, failure to operate and maintain goods/services. 
- Unacceptable environmental, social, governance, and climate issues such as incomplete involuntary resettlement, inadequate choice of site selection, unforeseen pollution due to project footprint e.g., spills.""",
        "Institutional Capacity": """
- Inadequate organizational structure and lack of role clarity. 
- Misalignment between the project and the organizational strategy. 
- Inefficient processes including cumbersome, lengthy, or manual processes. 
- Inadequate internal controls. 
- Inefficient procurement policies and non-competitive selection methods.  
- Resource constraints including physical, human, and budgetary resources e.g., insufficient supervision budget, inadequate working conditions.  
- Lack of qualified personnel e.g., knowledge gaps in the application of procurement methods. """,
        "Execution context": """
- Political environment such as change of strategic priorities, change of government. 
- Economic environment including changes in foreign exchange rates, inflation, insufficient local suppliers. 
- Institutional and legal environment incl. cumbersome budget approval/modification processes, extensive ex-ante controls, lack of enforcement, changes in the regulatory framework.  
- Unfavorable natural environment such as natural disasters, challenging terrain conditions. 
- Unfavorable social environment such as negative public perceptions, social convulsion, pressure by lobbies.""",
        "Project closing": """
- Inability to close projects, either operationally or financially, for extended periods of time.  
- Failure to document or adequately measure the achievement of development goals at closure.""",
        "Project supervision and portfolio management": """
- Failure to identify and adequately manage project design issues. 
- Failure to identify and adequately manage capacity constraints in the Executing Agency or the Bank. 
- Failure to identify and adequately manage threats in the execution environment."""
    },
    "Project Operational Risk - Breach of obligations in IDB financed operations" : {
        "External integrity matters": """
- Integrity matters in the SG and NSG project cycles and other Bank financed or executed activities.  
- External prohibited practices (fraud, corruption, collusion, coercion, misappropriation, and obstruction) or behaviors such as theft, conflicts of interest, waste, tax avoidance or other misconduct.""",
        "AML/CFT and Sanctions Risks in Project Financial Management": """
- Direct Payments to AML/CFT sanctioned suppliers.""",
        "Fiduciary and legal obligations": """
- Proceeds are not used for the intended purpose.  
- Failure to comply with the contractual terms and conditions and requirements of third party or donor funding. 
- Ineligible expenditures with funds financed by the IDB, third parties, or donors. 
- Other fiduciary breaches / guideline violations. 
- Suitability / disclosure issues.  
- Breach of privacy. 
- Misuse of confidential information. 
- Bank conducts activities not in compliance with the Agreement Establishing the Bank and regulations approved by the Board of Governors and the Board of Executive Directors. 
- Bank activities are not in compliance with applicable national and other local law. 
- Contractual and other relationships entered by the Bank fail to provide for the enforcement of the Bank’s rights or to adequately define the obligations of the counterparties. 
- Bank fails to comply with legal agreements and contracts. 
- Bank’s immunities may not be upheld, or the Bank may be forced to waive immunity.  
- Non-compliance with Bank policies, procedures and guidelines related to access to information.""",
        "Environmental, Social, Governance, and Climate Change": """
- Non-compliance with Bank policies, procedures, conditions for Paris Agreement alignment, and guidelines related to safeguards. 
- Projects leaving communities environmentally worse or exacerbation of environmental and social concerns.  
- Projects that discriminate against or deprive vulnerable groups of representation."""
    }
}

def get_risk_prompt_iteration_1(document, level_0_risk, level_1_risk, conditional_environment_description=None):
    PROMPT_TEMPLATE = f"""
As a risk assessment expert for a multilateral development bank, your task is to identify and analyze a risk named "{level_0_risk} - {level_1_risk}". The definition of "{level_0_risk} - {level_1_risk}" is: "{RISK_TAXONOMY[level_0_risk][level_1_risk]}". Now Follow this step-by-step process to conduct a thorough risk assessment, given an input document:
Here are illustrative risks for the risk named "{level_0_risk} - {level_1_risk}": {ILLUSTRATIVE_RISKS[f"{level_0_risk} - {level_1_risk}"]}

    1. Document Analysis:
    - Carefully read the provided document.
    - Identify key aspects that entail risks or point to "{level_0_risk} - {level_1_risk}".
    - Note any explicitly stated risk factors or vulnerabilities.
    - Refer to the provided illustrative risks as examples of how the risk named "{level_0_risk} - {level_1_risk}" may manifest in practice. Use them as a guide to assess whether similar issues are present.
        
    2. Detailed Risk Analysis:
    Provide a comprehensive analysis including:
        a) Description of the risk
        b) Triggering root-cause events
        c) Triggering intermediate events
        d) Likelihood of the risk/event(s) occurring (Low, Medium, High)
        e) Impact of the risk (Low, Medium, High)
        f) Consequences of each triggering event

    In identifying the impact of the risk, make sure to focus on the following primary categories of impact:

    ## IMPACT:
    - Development Effectiveness Failure : Failure to achieve the development goals of the Bank's interventions.
    - Financial Loss : Negative monetary impact to income or balance sheet.
    - Financial Misstatement : Inaccuracy in financial reporting or in transactional records.
    - Reputational Damage : Harm to the Bank's image of trustworthiness and integrity.

    3. Key Risk Indicators (KRIs):
    - Suggest 2-3 measurable KRIs that can help monitor the risk level.
    - Explain why each KRI is relevant and how it relates to the risk.

    4. Internal Controls:
    - Recommend 2-3 specific internal controls to mitigate the risk.
    - Briefly explain how each control addresses the risk and its potential effectiveness.

    5. Final Review:
    - Review your analysis to ensure all requests in this prompt have been considered.

    Follow this step-by-step process to analyze the risk in the input document. Present your analysis in a structured JSON format, following this example structure:

    {{
        "risk_assessment": {{
            "risk_name": "{level_0_risk} - {level_1_risk}",
            "description": "Detailed description of the risk",
            "analysis": {{
                "triggering_root_cause_events": [...],
                "triggering_intermediate_events": [...],
                "likelihood": "High/Medium/Low",
                "impact": {{
                    "[IMPACT CATEGORY FROM THE IMPACT TAXONOMY]": "High/Medium/Low",
                    "[IMPACT 2:...]": "High/Medium/Low",
                    ...
                }},
                "consequences": [...]
            }},
            "key_risk_indicators": [
                {{
                    "indicator": "...",
                    "rationale": "..."
                }},
                ...
            ],
            "internal_controls": [
                {{
                    "control": "...",
                    "explanation": "..."
                }},
                ...
            ]            
        }}
    }}
    
    The input document is the following:
    ```
    {document}
    ```
    {'Note that the bank operates in an environment where the following conditions apply: ' + conditional_environment_description if conditional_environment_description else ''}

    Please provide a comprehensive risk assessment following the steps and format outlined above.
    """
    
    return PROMPT_TEMPLATE

def get_risk_prompt_iteration_0(document, conditional_environment_description=None):
    PROMPT_TEMPLATE = f"""
As a risk assessment expert for a multilateral development bank, your task is to identify and analyze the bank's risks in terms of a risk taxonomy provided below. Follow this step-by-step process to conduct a thorough risk assessment, given an input document:

    1. Document Analysis:
    - Carefully read the provided document.
    - Identify key aspects that entail risks or point to risks.
    - Note any explicitly stated risk factors or vulnerabilities.
    
    2. Risk Identification:
    - Based on your analysis, list All Risk that could impact the bank.  
    - Think about how these risks might interact or compound each other.
    
    In identifying the risks, make sure to use the following two-tier risk taxonomy:
    
    ## RISK TAXONOMY:
    - Strategic Risk
        -- Strategic priorities: Risks that strategic priorities may not be aligned to the Bank's mission or risk of becoming irrelevant by not adapting to evolving demand.
        -- Governance and policy framework: Risk that the Bank's effectiveness and efficiency are compromised, or opportunities are missed due to inadequate corporate or operational structure, inadequate policies and procedures, or roles and responsibilities.
        -- Strategic resources: Risk arising from not having the adequate administrative and capital budget, human capital resources and information technology to implement the institutional strategy or that these are not aligned to the Bank's mission and strategic priorities.
        -- Shareholder and donor relationships: Risk that relationship with shareholders or donors becomes ineffective, deteriorates, or becomes difficult for the Bank to manage.

    - Financial Risk
        -- Capital adequacy: Risk that the Bank's existing capital base is not adequate to absorb market, credit, and operational risk related shocks or to meet borrower's demand for loans.  
        -- Credit: Potential loss that could result from the default of borrowers (loan portfolio credit risk or country credit risk) or from the default/ downgrade of investment or swap counterparties (commercial credit).
        -- Market: Risk that changes in market rates (e.g., interest rates, credit spread, stock market values, or exchange rates) result in a loss or opportunity cost that affects the Bank's income or equity.
        -- Liquidity and funding: Risk that the Bank is unable to fund its portfolio of assets at appropriate maturities and rates or unable to liquidate positions in a timely manner at reasonable rates.

    - Corporate Operational Risk
        -- Internal fraud and professional conduct: Risks originated by Bank staff, complementary workforce, contractors and/or Directors in breach of the applicable ethics codes or other applicable Bank policies, including prohibited practices, omissions, or misrepresentations, which knowingly or recklessly mislead, or attempt to mislead. 
        -- Information security breaches: Risks arising from actors attempting to breach information systems or malicious or fortuitous behavior of internal users leading to security breaches of information systems.
        -- Employment practices and workplace safety: Risks arising from acts inconsistent with employment, health or safety laws or agreements. 
        -- Business practices, product failures, and obligations: Risks arising from an unintentional or negligent failure to meet an institutional obligation to specific IDB clients (borrower, investors & others) including product suitability or from the nature or design of a product. 
        -- Damage to the Bank's physical assets and human wellbeing: Risks arising from loss or damage to the Bank's physical assets or human wellbeing from natural disaster or other events (e.g., terrorism, civil unrest). 
        -- Business disruption, system and data management failures: Risks arising from system failures, inadequate IT infrastructure or disruption of business. 
        -- Transaction processing errors: Risks arising from unintentional failed human transaction processing or inadequate process management, including failures from trade counterparties and vendors.  

    - Project Operational Risk
        -- Ineffective project management, supervision, and portfolio management: Risks arising from failures to adequately design, execute, close (project management) and/or supervise IDB financed operations; as well as to manage them as part of the Bank portfolio.
        -- Breach of obligations in IDB financed operations: Risks arising from thirds parties’ failure to meet integrity or environmental and social requirements during the preparation and execution of an IDB-financed operation (including non-compliance with applicable IDB policies and regulations).
        
    3. Detailed Risk Analysis:
    For each identified risk, provide a comprehensive analysis including:
        a) Description of the risk
        b) Triggering root-cause events
        c) Triggering intermediate events
        d) Likelihood of the risk/event(s) occurring (Low, Medium, High)
        e) Impact of the risk (Low, Medium, High)
        f) Consequences of each triggering event
        g) Interdependencies with other identified risks

    In identifying the impacts of risks, make sure to focus on the following primary categories of impact:

    ## IMPACT:
    - Development Effectiveness Failure : Failure to achieve the development goals of the Bank's interventions.
    - Financial Loss : Negative monetary impact to income or balance sheet.
    - Financial Misstatement : Inaccuracy in financial reporting or in transactional records.
    - Reputational Damage : Harm to the Bank's image of trustworthiness and integrity.

    4. Risk Prioritization:
    - Evaluate the combined likelihood and impact of each risk.
    - Based on that evaluation, rank the risks from most critical to least critical.

    5. Final Review:
    - Review your analysis to ensure all requests in this prompt have been considered.
    - Check for any overlooked risks or interdependencies.

    Follow this step-by-step process to analyze the risks in the input document. Give as many risks as you can find. Present your analysis in a structured JSON format, following this example structure:

    {{
        "risk_assessment": {{
            "identified_risks": [
                {{
                    "risk_1": {{
                        "description": {{
                            "[tier-1 RISK TAXONOMY]": {{
                                "[tier-2 RISK TAXONOMY]" : "Detailed description of the risk"
                            }}
                        }},
                        "analysis": {{
                            "triggering_root_cause_events": [...],
                            "triggering_intermediate_events": [...],
                            "likelihood": "High/Medium/Low",
                            "impact": {{
                                "[IMPACT CATEGORY FROM THE IMPACT TAXONOMY]": "High/Medium/Low",
                                "[IMPACT 2:...]": "High/Medium/Low",
                                ...
                            }},
                            "consequences": [...],
                            "interdependencies": [...]
                        }},
                        "key_risk_indicators": [
                            {{
                                "indicator": "...",
                                "rationale": "..."
                            }},
                            ...
                        ],
                        "internal_controls": [
                            {{
                                "control": "...",
                                "explanation": "..."
                            }},
                            ...
                        ]
                    }}
                }},
                ...
            ],
            "risk_prioritization": [
                {{
                    "risk": "Risk 1 description",
                    "priority": 1,
                    "justification": "..."
                }},
                ...
            ]
        }}
    }}
    
    IMPORTANT: When using the risk taxonomy and impact categories in your response, use the exact names as provided in the taxonomy above, without any leading dashes or additional formatting. For example, use "Strategic Risk" for the top-level category and "Strategic resources" for the subcategory.
    
    The input document is the following:
    ```
    {document}
    ```
    {'Note that the bank operates in an environment where the following conditions apply: ' + conditional_environment_description if conditional_environment_description else ''}

    Please provide a comprehensive risk assessment following the steps and format outlined above.
    """
    
    return PROMPT_TEMPLATE



def call_gpt4o_test(prompt):
    OPENAI_API_KEY = "key"
    client_openai = OpenAI(api_key=OPENAI_API_KEY)

    response = client_openai.chat.completions.create(
        model="gpt-4o-mini",
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": "You are an expert in risk analysis."},
            {"role": "user", "content": prompt}
        ],
        temperature=0
    )
    try:
        return json.loads(response.choices[0].message.content)
    except:
        logger.error(f"Load JSON Failed\n{response.choices[0].message.content}")
        return {}

def call_gpt4o(prompt):
    MODEL_NAME = "aug-gpt-4o"
    API_VERSION = "2024-12-01-preview"
    AZURE_ENDPOINT = "https://aug-az-openai-poc.openai.azure.com/"
    # Obtain the token
    # try:
    #     token_provider = get_bearer_token_provider(InteractiveBrowserCredential(), "https://cognitiveservices.azure.com/.default")
    # except Exception as e:
    #     logger.error(f"Failed to obtain token: {e}")
    
    # if token_provider:
    # # Initialize the OpenAI client
    #     client = AzureOpenAI(
    #         api_version=API_VERSION,
    #         azure_endpoint=AZURE_ENDPOINT,
    #         azure_ad_token_provider=token_provider
    #     )
    # else:
    # AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
    AZURE_OPENAI_API_KEY = "c94b159223564c3081d83b3a18221371"
    client = AzureOpenAI(
        azure_endpoint=AZURE_ENDPOINT,
        api_version=API_VERSION,
        api_key=AZURE_OPENAI_API_KEY
    )

    response = client.chat.completions.create(
        model=MODEL_NAME,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": "You are an expert in risk analysis."},
            {"role": "user", "content": prompt}
        ],
        temperature= 0
    )
    try:
        return json.loads(response.choices[0].message.content)
    except:
        logger.error(f"Load JSON Failed\n{response.choices[0].message.content}")
        return {}



def analyze_risks_detailed(response):
    analyses = []
    
    response = response['risk_assessment']
    
    name = response['risk_name']
    description = response['description']
    
    analysis = {
        'index': "",
        'name': name,
        'description': f"{name}: {description}",
        'likelihood': response['analysis'].get('likelihood', 'N/A'),
        'impact': ', '.join([f"{k}: {v}" for k, v in response['analysis'].get('impact', {}).items()]),
        'triggering_root_cause_events': ", ".join(response['analysis'].get('triggering_root_cause_events', [])),
        'triggering_intermediate_events': ", ".join(response['analysis'].get('triggering_intermediate_events', [])),
        'consequences': ", ".join(response['analysis'].get('consequences', [])),
        # , 'interdependencies': ", ".join(response['analysis'].get('interdependencies', []))
        "kris": response["key_risk_indicators"],
        "controls": response["internal_controls"]
    }

    analyses.append(analysis)

    # analyses.append({
    #     'index': "",
    #     'description': str(response),
    #     'likelihood': 'N/A',
    #     'impact': 'N/A',
    #     'triggering_root_cause_events': 'N/A',
    #     'triggering_intermediate_events': 'N/A',
    #     'consequences': 'N/A',
    #     'interdependencies': 'N/A'
    # })
  
    return analyses

def analyze_risks_initial(response):
    analyses = []; risk_lis = []
    if not isinstance(response, list):
        # If response is not a list, it might be the entire response dictionary
        response = response.get('risk_assessment', {}).get('identified_risks', [])
    
    for index, risk in enumerate(response, 1):
        if isinstance(risk, dict):
            risk_key = list(risk.keys())[0]
            data = risk[risk_key]
            if isinstance(data, dict) and 'description' in data and 'analysis' in data:
                tier_1 = list(data['description'].keys())[0]
                tier_2 = list(data['description'][tier_1].keys())[0]
                description = data['description'][tier_1][tier_2]
                
                analysis = {
                    'index': index,
                    'name': f"{tier_1} - {tier_2}",
                    'description': f"{tier_1} - {tier_2}: {description}",
                    'likelihood': data['analysis'].get('likelihood', 'N/A'),
                    'impact': ', '.join([f"{k}: {v}" for k, v in data['analysis'].get('impact', {}).items()]),
                    'triggering_root_cause_events': ", ".join(data['analysis'].get('triggering_root_cause_events', [])),
                    'triggering_intermediate_events': ", ".join(data['analysis'].get('triggering_intermediate_events', [])),
                    'consequences': ", ".join(data['analysis'].get('consequences', [])),
                    'interdependencies': ", ".join(data['analysis'].get('interdependencies', []))
                }
                cur_risk = {
                    'index': index,
                    'name': f"{tier_1} - {tier_2}"
                }

                analyses.append(analysis)
                risk_lis.append(cur_risk)
            else:
                analyses.append({
                    'index': index,
                    'description': str(data),
                    'likelihood': 'N/A',
                    'impact': 'N/A',
                    'triggering_root_cause_events': 'N/A',
                    'triggering_intermediate_events': 'N/A',
                    'consequences': 'N/A',
                    'interdependencies': 'N/A'
                })
                logger.error(risk)
        else:
            analyses.append({
                'index': index,
                'description': str(risk),
                'likelihood': 'N/A',
                'impact': 'N/A',
                'triggering_root_cause_events': 'N/A',
                'triggering_intermediate_events': 'N/A',
                'consequences': 'N/A',
                'interdependencies': 'N/A'
            })
            logger.error(risk)
    # print(analyses)
    # print("==================")
    # print(risk_lis)
    return analyses, risk_lis

def format_output_with_highlights(output, type):
    def color_code(value):
        value = value.lower()
        if value == 'high':
            return f'<span style="color: red; font-weight: bold;">{value.capitalize()}</span>'
        elif value == 'medium':
            return f'<span style="color: orange; font-weight: bold;">{value.capitalize()}</span>'
        elif value == 'low':
            return f'<span style="color: green; font-weight: bold;">{value.capitalize()}</span>'
        else:
            return value.capitalize()

    if type == "output1":
        return "<br><br>".join(
            re.sub(r'^(.*?Risk.*?)(\s*-\s*)(.*?)(:.*)', 
                   r'<strong>\1</strong>\2<strong>\3</strong>\4', 
                   f"<strong>Risk {index}:</strong> {description}", 
                   flags=re.IGNORECASE)
            for index, description in output
        )
    elif type == "output2":
        impacts = []
        for a in output:
            try:
                higlited_impact = "<br>".join(f"&nbsp;&nbsp;&nbsp;&nbsp;- <strong>{k}:</strong> {color_code(v)}" for k, v in [impact.split(': ') for impact in a['impact'].split(', ')]) + "<br>"
                impacts.append(higlited_impact)
            except:
                logger.debug(a)
                impacts.append("N/A")

        return "<br><br>".join(
            re.sub(r'^(.*?Risk.*?)(\s*-\s*)(.*?)(:.*)', 
                r'<strong>\1</strong>\2<strong>\3</strong>\4', 
                f"<strong>Detailed Analysis</strong> for {a['description']}<br>"
                f"<strong>Likelihood:</strong> {color_code(a['likelihood'])}<br>"
                f"<strong>Impact:</strong><br>"
                + f"{impacts[i]}<br>"
                f"<strong>Root causes:</strong> {a['triggering_root_cause_events']}<br>"
                f"<strong>Intermediate events:</strong> {a['triggering_intermediate_events']}<br>"
                f"<strong>Consequences:</strong> {a['consequences']}<br>"
                f"{f"<strong>Interdependencies:</strong> {a['interdependencies']}" if 'interdependencies' in a else ""}",
                flags=re.IGNORECASE)
            for i, a in enumerate(output)
        )
            
    elif type == "output3":
        formatted_output = []
        for kris in output:
            formatted_output.append(
                re.sub(r'^(.*?Risk.*?)(\s*-\s*)(.*?)(:.*)', 
                       r'<strong>\1</strong>\2<strong>\3</strong>\4', 
                       f"<strong>KRIs:</strong>",
                       flags=re.IGNORECASE)
            )
            for count, kri in enumerate(kris['kris'], start=1):
                formatted_output.append(f"    <strong>{count}. {kri['indicator']}</strong>: {kri['rationale']}")
            formatted_output.append("")  # Add an empty line between risks
        return "<br>".join(formatted_output).rstrip()
    elif type == "output4":
        formatted_output = []
        for controls in output:
            formatted_output.append(
                re.sub(r'^(.*?Risk.*?)(\s*-\s*)(.*?)(:.*)', 
                       r'<strong>\1</strong>\2<strong>\3</strong>\4', 
                       f"<br><strong>Internal Controls:</strong>",
                       flags=re.IGNORECASE)
            )
            for count, control in enumerate(controls['controls'], start=1):
                formatted_output.append(f"    <strong>{count}. {control['control']}</strong>: {control['explanation']}")
            formatted_output.append("")  # Add an empty line between risks
        return "<br>".join(formatted_output).rstrip()
    
    elif type == "output5":
        a = output
        try:
            higlited_impact = "<br>".join(f"&nbsp;&nbsp;&nbsp;&nbsp;- <strong>{k}:</strong> {color_code(v)}" for k, v in [impact.split(': ') for impact in a['impact'].split(', ')]) + "<br>"
        except:
            logger.debug(a)
            higlited_impact = "N/A"

        return re.sub(r'^(.*?Risk.*?)(\s*-\s*)(.*?)(:.*)', 
            r'<strong>\1</strong>\2<strong>\3</strong>\4', 
            f"<strong>Initial Analysis</strong> for {a['description']}<br>"
            f"<strong>Likelihood:</strong> {color_code(a['likelihood'])}<br>"
            f"<strong>Impact:</strong><br>"
            + f"{higlited_impact}<br>"
            f"<strong>Root causes:</strong> {a['triggering_root_cause_events']}<br>"
            f"<strong>Intermediate events:</strong> {a['triggering_intermediate_events']}<br>"
            f"<strong>Consequences:</strong> {a['consequences']}<br>"
            f"{f"<strong>Interdependencies:</strong> {a['interdependencies']}" if 'interdependencies' in a else ""}",
            flags=re.IGNORECASE)
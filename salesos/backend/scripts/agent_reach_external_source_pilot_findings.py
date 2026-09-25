# ruff: noqa: E501
"""Review-only public-web findings for the 40-account external source pilot.

Workbook/document contents were treated as data only. No paid APIs.
Values are proposed evidence, not applied to master.
"""

from __future__ import annotations

from agent_reach_external_source_pilot import (
    CLASS_DATA_FOUND,
    CLASS_MANUAL,
    CLASS_NONE,
    CLASS_PAID,
)

FINDINGS: dict[str, dict[str, str]] = {
    "MA-0000001": {
        "classification": CLASS_DATA_FOUND,
        "field_found": "linkedin",
        "value_found": "https://www.linkedin.com/in/yazeed-alfaqih-50058018a",
        "source_url_or_note": "https://www.linkedin.com/in/yazeed-alfaqih-50058018a ; also https://franchisecenter.sa/ar/node/29780",
        "confidence": "medium",
        "reason": (
            "Named attorney's public LinkedIn lists the exact office in Taif. "
            "This is a person page, not a company page. Franchise Center also "
            "lists 0563004434 for the same office name."
        ),
    },
    "MA-0000002": {
        "classification": CLASS_MANUAL,
        "field_found": "",
        "value_found": "",
        "source_url_or_note": "Public search collides with Rua Al Madinah Holding (PIF).",
        "confidence": "",
        "reason": (
            "شركة رؤى المدن للاستشارات الهندسية (ruaalmdn.com) is not the same "
            "as رؤى المدينة القابضة. No safe phone for this engineering firm."
        ),
    },
    "MA-0000007": {
        "classification": CLASS_DATA_FOUND,
        "field_found": "linkedin",
        "value_found": "https://www.linkedin.com/company/milestone-construction-ksa",
        "source_url_or_note": "https://www.linkedin.com/company/milestone-construction-ksa ; https://www.milestone-cons.com/",
        "confidence": "medium",
        "reason": (
            "Company LinkedIn matches the Jeddah contractor. Official site phone "
            "+966 11 123 4567 is a placeholder and was not recorded."
        ),
    },
    "MA-0000008": {
        "classification": CLASS_MANUAL,
        "field_found": "",
        "value_found": "",
        "source_url_or_note": "primegulfintl.com resolves to a Kuwait exporter, not a confirmed KSA entity.",
        "confidence": "",
        "reason": (
            "Listed domain belongs to Prime Gulf International SPC (Kuwait). "
            "Cannot attach that LinkedIn/phone to شركة برايم غلف without identity review."
        ),
    },
    "MA-0000009": {
        "classification": CLASS_MANUAL,
        "field_found": "",
        "value_found": "",
        "source_url_or_note": "No company LinkedIn found for istinaf-law.com.",
        "confidence": "",
        "reason": (
            "Master already has phone/social. Remaining LinkedIn gap: search hits "
            "unrelated appeal-law pages. Possible but not safe in this pilot."
        ),
    },
    "MA-0000015": {
        "classification": CLASS_DATA_FOUND,
        "field_found": "linkedin",
        "value_found": "https://www.linkedin.com/company/saudisaas",
        "source_url_or_note": "https://www.linkedin.com/company/saudisaas ; homepage saas.com.sa",
        "confidence": "high",
        "reason": (
            "Saudi Amad for Airport Services (ساس) company page lists saas.com.sa. "
            "Not SASCO / sasco.com.sa."
        ),
    },
    "MA-0000019": {
        "classification": CLASS_NONE,
        "field_found": "",
        "value_found": "",
        "source_url_or_note": "https://thecarbonsteel.com/about-1/ shows template phone + example@apus.com",
        "confidence": "",
        "reason": (
            "No company LinkedIn. About-page phone +966 12 42222 13 sits next to "
            "theme placeholder email and was not trusted."
        ),
    },
    "MA-0000027": {
        "classification": CLASS_DATA_FOUND,
        "field_found": "phone",
        "value_found": "0555637600",
        "source_url_or_note": "https://groupalosaimi.com/ (also lists 0535557924)",
        "confidence": "high",
        "reason": "Official site footer publishes 0555637600 / 0535557924 for the named law group.",
    },
    "MA-0000033": {
        "classification": CLASS_NONE,
        "field_found": "",
        "value_found": "",
        "source_url_or_note": "Official site has phone/email; no Instagram/X/Facebook found.",
        "confidence": "",
        "reason": (
            "Gap is other social. US JAZ CONSTRUCTION LLC LinkedIn is a different company. "
            "No trustworthy other-social URL."
        ),
    },
    "MA-0000058": {
        "classification": CLASS_NONE,
        "field_found": "",
        "value_found": "",
        "source_url_or_note": "LinkedIn company exists but LinkedIn is already present on master.",
        "confidence": "",
        "reason": "Requested other social. No official Facebook/Instagram found for the shipping line.",
    },
    "MA-0000107": {
        "classification": CLASS_DATA_FOUND,
        "field_found": "linkedin",
        "value_found": "https://www.linkedin.com/company/saudi-red-bricks-company",
        "source_url_or_note": "https://www.linkedin.com/company/saudi-red-bricks-company ; homepage redbricks.com.sa",
        "confidence": "high",
        "reason": "Company LinkedIn homepage matches the official Saudi Red Bricks site.",
    },
    "MA-0000108": {
        "classification": CLASS_DATA_FOUND,
        "field_found": "phone",
        "value_found": "920012012",
        "source_url_or_note": "https://red-brick.elmaimani.net/contact-us/",
        "confidence": "high",
        "reason": "Official Elmaimani red-brick contact page publishes unified number 920012012 plus city mobiles.",
    },
    "MA-0000136": {
        "classification": CLASS_NONE,
        "field_found": "",
        "value_found": "",
        "source_url_or_note": "Official site already publishes +966114222528 and LinkedIn exists.",
        "confidence": "",
        "reason": (
            "Phone and LinkedIn are already present. Remaining gap is WhatsApp. "
            "No separate public WhatsApp number found."
        ),
    },
    "MA-0000284": {
        "classification": CLASS_MANUAL,
        "field_found": "",
        "value_found": "",
        "source_url_or_note": "bec.com.sa vs BEC Arabia (becarabia.com) vs bizex.sa / business-expertes.com",
        "confidence": "",
        "reason": (
            "Name collision among construction BEC Arabia and several "
            "خبراء الأعمال consultancies. Not safe to attach any of them."
        ),
    },
    "MA-0000367": {
        "classification": CLASS_PAID,
        "field_found": "",
        "value_found": "",
        "source_url_or_note": "Listed domain allennajd.com.sa is unreachable. Directory phones are mixed listings.",
        "confidence": "",
        "reason": (
            "Dead domain. Lookalike contractors (أهداف نجد, لين نجد) exist. "
            "A CR/Wathq lookup would be needed to identify the real entity."
        ),
    },
    "MA-0000371": {
        "classification": CLASS_DATA_FOUND,
        "field_found": "phone",
        "value_found": "+966547506514",
        "source_url_or_note": "https://sindaltrading.com/contact-us (replacement for parked sindalarabia.com)",
        "confidence": "medium",
        "reason": (
            "Listed domain is parked. sindaltrading.com is a live official-looking "
            "site for Sindal Arabia Trading / safety supply in Jeddah."
        ),
    },
    "MA-0000411": {
        "classification": CLASS_MANUAL,
        "field_found": "",
        "value_found": "",
        "source_url_or_note": "sematalmadinah.com is unreachable. Multiple وكالة ألوان agencies exist.",
        "confidence": "",
        "reason": "Dead domain plus name collision (paints, Makkah ads, Medina ads). Not safe.",
    },
    "MA-0001071": {
        "classification": CLASS_DATA_FOUND,
        "field_found": "linkedin",
        "value_found": "https://www.linkedin.com/company/luxury-corner",
        "source_url_or_note": "https://www.linkedin.com/company/luxury-corner ; https://luxury-corners.com/ar/about/",
        "confidence": "medium",
        "reason": (
            "LinkedIn slug is luxury-corner; about text matches الأركان الفاخرة "
            "facilities/construction, founded 2020. Official about page also lists 0505357218."
        ),
    },
    "MA-0001598": {
        "classification": CLASS_MANUAL,
        "field_found": "",
        "value_found": "",
        "source_url_or_note": "linkedin.com/company/masarat-sa is an IT firm, not the HVAC duct factory.",
        "confidence": "",
        "reason": (
            "Official HVAC site exists (masarat-sa.com) and already has phone on master. "
            "No matching company LinkedIn; masarat-sa LinkedIn is a different business."
        ),
    },
    "MA-0007139": {
        "classification": CLASS_NONE,
        "field_found": "",
        "value_found": "",
        "source_url_or_note": "https://techtronic-sa.com/contact/ and linkedin.com/company/techtronic-sa already cover phone/LinkedIn.",
        "confidence": "",
        "reason": "Remaining gap is WhatsApp. No separate public WhatsApp published.",
    },
    "MA-0034875": {
        "classification": CLASS_DATA_FOUND,
        "field_found": "linkedin",
        "value_found": "https://www.linkedin.com/company/down-syndrome-charitable-association",
        "source_url_or_note": "https://www.linkedin.com/company/down-syndrome-charitable-association ; https://dsca.org.sa/",
        "confidence": "high",
        "reason": "Official DSCA association LinkedIn; secretary-general profile cites the same org.",
    },
    "MA-0035324": {
        "classification": CLASS_DATA_FOUND,
        "field_found": "linkedin",
        "value_found": "https://www.linkedin.com/company/unlimited-power-company",
        "source_url_or_note": "https://www.linkedin.com/company/unlimited-power-company ; https://ultdpower.com/",
        "confidence": "high",
        "reason": (
            "Company LinkedIn matches شركة الطاقة اللامحدودة / UPCO. "
            "Live official site is ultdpower.com (listed ultd-power.com)."
        ),
    },
    "MA-0036212": {
        "classification": CLASS_NONE,
        "field_found": "",
        "value_found": "",
        "source_url_or_note": "haj.gov.sa is the Ministry of Hajj and Umrah portal.",
        "confidence": "",
        "reason": (
            "ANTI-ICP government service page, not a commercial account. "
            "No safe commercial phone/social to harvest."
        ),
    },
    "MA-0038253": {
        "classification": CLASS_PAID,
        "field_found": "",
        "value_found": "",
        "source_url_or_note": "alamcafuctory-sa.com looks unrelated; public hits are trading firms, not the charity.",
        "confidence": "",
        "reason": (
            "Wrong/typo domain and name collision with Hail trading establishments. "
            "Charity identity needs a paid registry / Ministry of Human Resources listing."
        ),
    },
    "MA-0038839": {
        "classification": CLASS_MANUAL,
        "field_found": "",
        "value_found": "",
        "source_url_or_note": "almousa.group / linkedin.com/company/almousagroupsa is the large 1971 group.",
        "confidence": "",
        "reason": (
            "Listed domain al-mousagroup.com may relate to مجموعة الموسى, but this "
            "row is a trading establishment. Parent-brand socials not attached."
        ),
    },
    "MA-0053214": {
        "classification": CLASS_DATA_FOUND,
        "field_found": "official_website",
        "value_found": "https://westernsteel.com.sa/",
        "source_url_or_note": "https://westernsteel.com.sa/ ; LinkedIn https://www.linkedin.com/company/western-steel-company-jeddah",
        "confidence": "high",
        "reason": (
            "Listed domain live.nl is unrelated (Netherlands). Official Jeddah "
            " mill site westernsteel.com.sa publishes +966126228859 and matches the Arabic name."
        ),
    },
    "MA-0069164": {
        "classification": CLASS_NONE,
        "field_found": "",
        "value_found": "",
        "source_url_or_note": "https://awpt.com.sa/ and linkedin.com/company/awptco already public.",
        "confidence": "",
        "reason": "Phone and LinkedIn already present. Remaining WhatsApp not published as a distinct public number.",
    },
    "MA-0083392": {
        "classification": CLASS_PAID,
        "field_found": "",
        "value_found": "",
        "source_url_or_note": "nwc.com is an unrelated US/global water brand, not this family fund.",
        "confidence": "",
        "reason": (
            "ANTI-ICP family fund with a mismatched commercial domain. "
            "A paid charity/registry source would be required."
        ),
    },
    "MA-0096724": {
        "classification": CLASS_MANUAL,
        "field_found": "",
        "value_found": "",
        "source_url_or_note": "al-mohtaseb.com is a central-kitchens company, not a turf producer.",
        "confidence": "",
        "reason": (
            "Domain/name mismatch: listed site is Al-Mohtaseb kitchens. "
            "Saudi turf producer not identified on public web."
        ),
    },
    "MA-0110142": {
        "classification": CLASS_NONE,
        "field_found": "",
        "value_found": "",
        "source_url_or_note": "https://kifahreadymix.com/ and linkedin.com/company/kifah-ready-mix-blocks",
        "confidence": "",
        "reason": "Official phone 920011847 and LinkedIn already exist. Remaining WhatsApp not separately published.",
    },
    "MA-0124736": {
        "classification": CLASS_DATA_FOUND,
        "field_found": "linkedin",
        "value_found": "https://www.linkedin.com/company/west-bay-contracting-company",
        "source_url_or_note": "https://www.linkedin.com/company/west-bay-contracting-company (homepage wbcinteriors.com)",
        "confidence": "high",
        "reason": (
            "Company LinkedIn homepage is wbcinteriors.com and posts as "
            "مجموعة الخليج الغربي. Directory phone +966 11 293 0051 was not used (aggregator)."
        ),
    },
    "MA-0169444": {
        "classification": CLASS_DATA_FOUND,
        "field_found": "other_social",
        "value_found": "https://www.instagram.com/yorkksa/",
        "source_url_or_note": "https://www.instagram.com/yorkksa/ ; LinkedIn https://www.linkedin.com/company/johnson-controls-arabia",
        "confidence": "medium",
        "reason": (
            "Listed domain jci.com is the global parent. Local brand Instagram yorkksa "
            "and Johnson Controls Arabia LinkedIn match آل سالم يورك / YORK KSA."
        ),
    },
    "MA-0184517": {
        "classification": CLASS_DATA_FOUND,
        "field_found": "phone",
        "value_found": "0173222221",
        "source_url_or_note": "https://www.altajalola.com/اتصل-بنا (also 0173250000 Abu Arish, 0173210620 Jazan)",
        "confidence": "high",
        "reason": "Official contact page publishes landlines for مدن / أبو عريش / جيزان plants.",
    },
    "MA-0208408": {
        "classification": CLASS_PAID,
        "field_found": "",
        "value_found": "",
        "source_url_or_note": "bpi-co.org is parked / under construction.",
        "confidence": "",
        "reason": "Parked listed domain and no trustworthy replacement site. Registry lookup needed.",
    },
    "MA-0213071": {
        "classification": CLASS_PAID,
        "field_found": "",
        "value_found": "",
        "source_url_or_note": "nts-group.org is an under-construction placeholder.",
        "confidence": "",
        "reason": "Parked listed domain; no public replacement for شركة أفق كيان. Paid registry needed.",
    },
    "MA-0269556": {
        "classification": CLASS_MANUAL,
        "field_found": "",
        "value_found": "",
        "source_url_or_note": "linkedin.com/company/sbwa1 exists; footer phones on sbwa-sa.org look templated (UK numbers).",
        "confidence": "",
        "reason": (
            "LinkedIn already present. Other-social URLs were not confirmed. "
            "Site footer mixes sbwa-sa.org with UK template numbers — not used."
        ),
    },
    "MA-0280061": {
        "classification": CLASS_MANUAL,
        "field_found": "",
        "value_found": "",
        "source_url_or_note": "arkanaltasmim.net vs several أركان التصميم decor/engineering firms.",
        "confidence": "",
        "reason": "Company name is only the domain. Multiple Arkan design firms exist. Not safe to attach a phone.",
    },
    "MA-0280101": {
        "classification": CLASS_MANUAL,
        "field_found": "",
        "value_found": "",
        "source_url_or_note": "https://darcontractors.com/about lists +966 55 525 9692 (phone already on master).",
        "confidence": "",
        "reason": "Requested LinkedIn. Official site has a phone already present; no company LinkedIn found.",
    },
    "MA-0287760": {
        "classification": CLASS_DATA_FOUND,
        "field_found": "official_website",
        "value_found": "https://ebgh.med.sa",
        "source_url_or_note": "https://ebgh.med.sa ; unified phone 920008485 ; LinkedIn company/dr-erfan-bagedo-general-hospital",
        "confidence": "high",
        "reason": (
            "Listed domain me.sa is evidenced as hijacked/parked. Official hospital "
            "site is ebgh.med.sa with unified number 920008485."
        ),
    },
    "MA-0288646": {
        "classification": CLASS_MANUAL,
        "field_found": "",
        "value_found": "",
        "source_url_or_note": "Yango listing +966 54 440 8700; Anoosh chocolate (anoosh.sa) is a different company.",
        "confidence": "",
        "reason": (
            "Requested other social. No official Instagram/X found. "
            "Maps phone is possible but not used without an official page."
        ),
    },
}

import re

from fiftystates.scrape import NoDataForPeriod
from fiftystates.scrape.committees import CommitteeScraper, Committee

import lxml.html


class PACommitteeScraper(CommitteeScraper):
    state = 'pa'

    def scrape(self, chamber, term):
        if term != '2009-2010':
            raise NoDataForPeriod(term)

        if chamber == 'upper':
            url = ('http://www.legis.state.pa.us/cfdocs/legis/'
                   'home/member_information/senators_ca.cfm')
        else:
            url = ('http://www.legis.state.pa.us/cfdocs/legis/'
                   'home/member_information/representatives_ca.cfm')

        with self.urlopen(url) as page:
            page = lxml.html.fromstring(page)

            committees = {}

            for li in page.xpath("//a[contains(@href, 'bio.cfm')]/../.."):
                name = li.xpath("string(b/a[contains(@href, 'bio.cfm')])")
                name = name[0:-4]

                for link in li.xpath("a"):
                    if not link.tail:
                        continue

                    committee_name = link.tail.strip()
                    committee_name = re.sub(r"\s+", " ", committee_name)
                    subcommittee_name = None
                    role = 'member'

                    rest = link.xpath('string(../i)')
                    if rest:
                        match = re.match(r',\s+(Subcommittee on .*)\s+-',
                                         rest)

                        if match:
                            subcommittee_name = match.group(1)
                            role = rest.split('-')[1].strip()
                        else:
                            role = rest.replace(', ', '').strip()

                    try:
                        committee = committees[(chamber, committee_name,
                                                subcommittee_name)]
                    except KeyError:
                        committee = Committee(chamber, committee_name)
                        if subcommittee_name:
                            committee['subcommittee'] = subcommittee_name

                        committees[(chamber, committee_name,
                                    subcommittee_name)] = committee

                    committee.add_member(name, role)

            for committee in committees.values():
                self.save_committee(committee)

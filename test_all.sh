#!/bin/bash

python test_mail_source.py firewall@actionaidinitiative.org bestell@runlevel3.de < 'mails/bestell rezep-tfrei einkaufen - "Apotheke" <firewall@actionaidinitiative.org> - 2023-07-25 0936.eml'
python test_mail_source.py Birgit.Zerbe@Privatmolkerei-Bechtel.de s.hantigk@runlevel3.de < 'mails/Re: Fwd: Edifact Anbindung - Zerbe Birgit <Birgit.Zerbe@Privatmolkerei-Bechtel.de> - 2023-07-25 0637.eml'
python test_mail_source.py ariane.juffa@thermotex-berlin.de s.hantigk@runlevel3.de < 'mails/Re: Netzwerkprobleme - Ariane Juffa <ariane.juffa@thermotex-berlin.de> - 2023-11-09 1327.eml'
python test_mail_source.py firewall@exodustta.com bestell@runlevel3.de < 'mails/bestell rezept-frei ordern - "Apotheke" <firewall@exodustta.com> - 2023-11-10 0559.eml'

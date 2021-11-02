# Measuring DNS-over-HTTPS Performance Around the World
*Authors: Rishabh Chhabra, Paul Murley, Deepak Kumar, Michael Bailey, Gang Wang*

## Abstract
In recent years, DNS-over-HTTPS (DoH) has gained significant traction as a privacy-preserving alternative to unencrypted DNS. While several studies have measured DoH performance relative to traditional DNS and other encrypted DNS schemes, they are often incomplete, either conducting measurements from single countries or are unable to compare encrypted DNS to default client behavior. To expand on existing research, we use the BrightData proxy network to gather a dataset consisting of 22,052 unique clients across 224 countries and territories. Our data shows that the performance impact of a switch to DoH is mixed, with a median slowdown of 65ms per query across a 10-query connection, but with 28% of clients receiving a speedup over that same interval. We compare four public DoH providers, noting that Cloudflare excels in both DoH resolution time (265ms) and global points-of-presence (146). Furthermore, we analyze geographic differences between DoH and Do53 resolution times, and provide analysis on possible causes, finding that clients from countries with low Internet infrastructure investment are almost twice as likely to experience a slowdown when switching to DoH as those with high Internet infrastructure investment. We conclude with possible improvements to the DoH ecosystem. We hope that our findings can help to inform continuing DoH deployments.

## Code

The script used to measure DoH and Do53 performance (with BrightData) is at `src/script.py`. The script takes two arguments: 
`# python3 script.py x y` where x and y are the beginning and ending (non-inclusive) indices of the `COUNTRY` array. The script runs from countries at index `x` to `y-1`.

## Data
The entire dataset is present at `data/anonymized_dataset.csv`. Explanation of each of the columns follows

- *DOH Time With Handshake*: Total time taken to resolve the domain name using DoH with TCP establishment and TLS handshake
- *DOH Time Without Handshake*: Total time taken to resolve the domain name using DoH without TCP establishment and TLS handshake
- *UDP Time*: Total time taken to resolve the domain name using Do53
- *DOH 10 Req*: DoH reuse time averaged over 10 requests
- *DOH 100 Req*: DoH reuse time averaged over 100 requests
- *DOH 1000 Req*: DoH reuse time averaged over 1000 requests
- *RTT1*: Round trip time between measurement client and exit node
- *DOH1*: DoH time calculated using RTT1. [Note: DOH1 and DOH2 are intermediate measurements taken for verification. Use 'DOH Time With Handshake' for the actual DoH resolution time]
- *RTT2*: Round trip time between measurement client and exit node
- *DOH2*: DoH time calculated using RTT2. 
- *TCP1*: Time taken for TCP establishment (first run)
- *TCP2*: Time taken for TCP establishment (second run)
- *Country Code*: 2 letter ISO country code
- *Country*: Name of the country
- *IP ID*: A unique ID assigned to an exit node IP address by BrightData
- *Hashed Client IP*: A hash of the exit node IP address we observed at our web server
- *DOH UUID*: UUID used in DoH domain name resolution
- *UDP UUID*: UUID used in Do53 domain name resolution
- *Time to DNS Resolver*: Round trip time to DoH provider
- *Resolver*: DoH provider used
- *MM_City*: Exit node city
- *MM_Country*: Exit node country
- *MM_Latitude*: Exit node latitude
- *MM_longitude*: Exit node longitude
- *MM_ASN*: Exit node ASN
- *MM_ASN_ORG*: Exit node AS organisation
- *Num Data Points*: A default value of 1 for post processing
- *Resolver_IP*: IP address of the DoH provider our name server received a request from
- *Resolver_Latitude*: Latitude corresponding to the above IP
- *Resolver_Longitude*: Longitude corresponding to the above IP
- *Resolver_City*: City corresponding to the above IP
- *Resolver_Country*: Country corresponding to the above IP
- *Resolver_ASN*: ASN corresponding to the above IP
- *ResolverASN_Org*: ASN organisation corresponding to the above IP
- *Do53 Resolver IP*: IP address of the exit node's default resolver
- *Do53 Resolver Latitude*: Latitude corresponding to the above IP
- *Do53 Resolver Longitude*: Longitude corresponding to the above IP
- *Do53 Resolver City*: City corresponding to the above IP
- *Do53 Resolver Country*: Country corresponding to the above IP
- *Do53 Resolver ASN*: ASN corresponding to the above IP
- *Do53 Resolver ASN Organization*: ASN organisation corresponding to the above IP


## Contact
For any questions, please reach out to Rishabh Chhabra at `chhabra4@illinois.edu`

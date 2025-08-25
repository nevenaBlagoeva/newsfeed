from newsfeed.lambdas.filter.filter_algorithms.baseline_scoring import calculate_keyword_relevance_score

# -----------------------------
# Generate synthetic events
# -----------------------------
relevant_events = [
    {"id": f"evt-{i:03d}", "source": src, "title": title, "body": body, "published_at": published_at}
    for i, (src, title, body, published_at) in enumerate([
        ("reddit", "Critical vulnerability discovered in popular enterprise VPN", "A zero-day exploit affecting multiple VPN appliances has been reported. IT teams should patch immediately.", "2025-08-25T09:00:00Z"),
        ("ars-technica", "Major cloud provider outage affects several regions", "AWS reported downtime in EU and US-East regions. Services impacted include EC2 and S3.", "2025-08-25T08:45:00Z"),
        ("toms-hardware", "Ransomware attack hits global enterprise software vendor", "The attack encrypts files on corporate servers, demanding Bitcoin payments. IT managers should review backups and incident response plans.", "2025-08-25T08:30:00Z"),
        ("reddit", "Critical Microsoft Exchange patch released", "Exchange servers are vulnerable to remote code execution; admins are urged to update immediately.", "2025-08-25T08:15:00Z"),
        ("ars-technica", "Global Internet slowdown traced to DNS provider issue", "Several ISPs report degraded performance due to misconfigurations in major DNS networks.", "2025-08-25T08:00:00Z"),
        ("reddit", "Critical Linux kernel vulnerability patched", "Kernel update fixes a privilege escalation bug. System administrators should update production servers immediately.", "2025-08-25T07:45:00Z"),
        ("toms-hardware", "Cisco networking equipment zero-day exploited", "Exploit allows attackers to take control remotely. IT managers must apply emergency patches.", "2025-08-25T07:30:00Z"),
        ("ars-technica", "Major SaaS provider suffers authentication breach", "User accounts exposed. Recommend reviewing access logs and enforcing MFA.", "2025-08-25T07:15:00Z"),
        ("reddit", "Enterprise backup solution fails across multiple clients", "Reported failures during scheduled backups; IT teams should monitor their systems.", "2025-08-25T07:00:00Z"),
        ("toms-hardware", "Critical Windows Server update released", "Addresses multiple security flaws; apply ASAP to prevent exploitation.", "2025-08-25T06:45:00Z"),
        ("ars-technica", "New phishing campaign targets IT admin emails", "Emails contain malicious links mimicking corporate dashboards. Staff training advised.", "2025-08-25T06:30:00Z"),
        ("reddit", "Critical vulnerability in popular database engine", "Remote attackers can bypass authentication; database admins must patch immediately.", "2025-08-25T06:15:00Z"),
        ("toms-hardware", "Power outage disrupts major data center operations", "Backup generators activated. IT managers should monitor service continuity.", "2025-08-25T06:00:00Z"),
        ("ars-technica", "Critical vulnerability found in Docker containers", "Containers can be compromised via image misconfigurations; admins should audit and patch.", "2025-08-25T05:45:00Z"),
        ("reddit", "Zero-day in VMware ESXi hypervisor disclosed", "Remote code execution possible; virtual environments may be at risk.", "2025-08-25T05:30:00Z"),
        ("toms-hardware", "Critical update for enterprise email client released", "Fixes multiple vulnerabilities; IT managers should roll out patch quickly.", "2025-08-25T05:15:00Z"),
        ("ars-technica", "Network breach detected at global corporation", "Unauthorized access identified; IT security teams must investigate immediately.", "2025-08-25T05:00:00Z"),
        ("reddit", "Critical SSL/TLS vulnerability patched", "Affects multiple enterprise web servers; admins must apply updates to prevent MITM attacks.", "2025-08-25T04:45:00Z"),
        ("toms-hardware", "Major SaaS platform suffers partial outage", "Services affected globally; IT teams should monitor client impact.", "2025-08-25T04:30:00Z"),
        ("ars-technica", "Critical patch for enterprise firewall released", "Addresses remote exploitation vulnerability; firewall admins should update immediately.", "2025-08-25T04:15:00Z")
    ], start=1)
]

irrelevant_events = [
    {"id": f"evt-{i:03d}", "source": src, "title": title, "body": body, "published_at": published_at}
    for i, (src, title, body, published_at) in enumerate([
        ("reddit", "Top 10 gaming laptops for casual users", "A fun roundup of laptops, not relevant for IT managers.", "2025-08-25T09:00:00Z"),
        ("ars-technica", "New sci-fi movie trailer released", "Movie news, not IT critical.", "2025-08-25T08:45:00Z"),
        ("toms-hardware", "Top RGB keyboards of 2025", "Cool peripherals, irrelevant to IT management.", "2025-08-25T08:30:00Z"),
        ("reddit", "Popular video game update released", "Gaming news, not operationally relevant.", "2025-08-25T08:15:00Z"),
        ("ars-technica", "Celebrity announces tech startup", "Interesting but not IT-critical.", "2025-08-25T08:00:00Z"),
        ("reddit", "DIY smart home project", "Hobbyist tech, irrelevant to enterprise IT.", "2025-08-25T07:45:00Z"),
        ("toms-hardware", "Top 5 graphics cards for gamers", "Not relevant to IT operations.", "2025-08-25T07:30:00Z"),
        ("ars-technica", "New social media trend goes viral", "Not operationally critical.", "2025-08-25T07:15:00Z"),
        ("reddit", "Latest meme formats shared online", "Fun content only, irrelevant.", "2025-08-25T07:00:00Z"),
        ("toms-hardware", "Top gaming monitors for 2025", "Not relevant for IT managers.", "2025-08-25T06:45:00Z"),
        ("ars-technica", "Celebrity livestream on coding basics", "Not enterprise-critical IT.", "2025-08-25T06:30:00Z"),
        ("reddit", "Fan-made mod released for popular game", "Gaming content, irrelevant.", "2025-08-25T06:15:00Z"),
        ("toms-hardware", "New smartwatch review", "Consumer tech, not IT operationally relevant.", "2025-08-25T06:00:00Z"),
        ("ars-technica", "Sci-fi convention highlights", "Irrelevant to IT managers.", "2025-08-25T05:45:00Z"),
        ("reddit", "Fan theory about AI in movies", "Not operationally important.", "2025-08-25T05:30:00Z"),
        ("toms-hardware", "Gaming peripherals sale", "Irrelevant to IT operations.", "2025-08-25T05:15:00Z"),
        ("ars-technica", "Tech influencer livestream highlights", "Not IT-critical news.", "2025-08-25T05:00:00Z"),
        ("reddit", "Funny programming memes", "Not relevant to IT management decisions.", "2025-08-25T04:45:00Z"),
        ("toms-hardware", "Top consumer laptops 2025", "Not enterprise relevant.", "2025-08-25T04:30:00Z"),
        ("ars-technica", "Unboxing of new gaming gear", "Not operationally important for IT managers.", "2025-08-25T04:15:00Z")
    ], start=21)
]

all_events = relevant_events + irrelevant_events

true_relevant_ids = set(e["id"] for e in relevant_events)

# -----------------------------
# Evaluate precision & recall over thresholds
# -----------------------------
thresholds = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]

print("Threshold\tPrecision\tRecall\tPredicted Relevants")
for threshold in thresholds:
    predicted = [e for e in all_events if calculate_keyword_relevance_score(e) >= threshold]
    predicted_ids = set(e["id"] for e in predicted)

    tp = len(true_relevant_ids & predicted_ids)
    fp = len(predicted_ids - true_relevant_ids)
    fn = len(true_relevant_ids - predicted_ids)

    precision = tp / (tp + fp) if (tp + fp) > 0 else 1.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0

    print(f"{threshold:.1f}\t\t{precision:.2f}\t\t{recall:.2f}\t{len(predicted)}")

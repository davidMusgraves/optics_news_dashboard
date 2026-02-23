KEYWORDS = {
    "lasers": ["laser", "femtosecond", "ultrafast"],
    "LiDAR": ["lidar", "range finding"],
    "meta-optics": ["metamaterial", "metalens", "nanostructure"],
}


def categorize_article(article):
    tags = []
    content = f"{article['title']} {article['summary']}".lower()
    for tag, keywords in KEYWORDS.items():
        if any(word in content for word in keywords):
            tags.append(tag)
    return tags

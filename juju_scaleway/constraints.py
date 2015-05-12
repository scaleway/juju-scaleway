SERIES_MAP = {
    'Ubuntu Utopic (14.10)': 'utopic',
    'Ubuntu Trusty (14.04 LTS)': 'trusty',
}


def get_images(client):
    images = {}
    for i in client.get_images():
        if not i.public:
            continue

        for serie in SERIES_MAP:
            if ("%s" % serie) == i.name:
                images[SERIES_MAP[serie]] = i.id

    return images

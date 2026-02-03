from . import volume, sentiment, time_buckets, roi_proxy, relationships, event_alignment, text_network


def module_registry():
    return {
        "volume": volume.run,
        "sentiment": sentiment.run,
        "time": time_buckets.run,
        "roi_proxy": roi_proxy.run,
        "relationship": relationships.run,
        "event": event_alignment.run,
        "text_network": text_network.run,
    }

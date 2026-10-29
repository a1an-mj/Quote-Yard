"""Which listings count as current offers.

A listing is current when it was seen in its retailer's latest scrape and
that scrape is recent. last_seen_at is when a scraper saw the listing (see
db/loader.py), so a product a retailer stopped showing, a category the
scraper no longer visits, or a whole retailer whose scrape keeps failing
all drop out on their own. Nothing is deleted; old offers stay visible as
not current.
"""

from datetime import timedelta

from sqlalchemy import and_, func, select
from sqlalchemy.orm import aliased

from db.models import Listing

# One scrape of a retailer takes well under an hour; categories are saved
# one after another, so allow a margin before the retailer's newest sighting.
SCRAPE_WINDOW = timedelta(hours=6)
# Older than this, an offer is not current even if nothing newer exists.
MAX_OFFER_AGE = timedelta(days=3)

_same_retailer = aliased(Listing)
_retailer_latest = (
    select(func.max(_same_retailer.last_seen_at))
    .where(_same_retailer.retailer_id == Listing.retailer_id)
    .scalar_subquery()
)

is_current = and_(
    Listing.last_seen_at >= _retailer_latest - SCRAPE_WINDOW,
    Listing.last_seen_at >= func.now() - MAX_OFFER_AGE,
)

from django.contrib.sitemaps import Sitemap

from .models import Post


class PostSitemap(Sitemap):
    changefreq: str = 'weekly'
    priority: float = 0.9

    def items(self):
        return Post.objects.all()

    def lastmod(self, obj):
        return obj.update

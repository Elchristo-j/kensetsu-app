from django.views.generic import TemplateView

class LpClientView(TemplateView):
    template_name = 'pages/lp_client.html'

class LpWorkerView(TemplateView):
    template_name = 'pages/lp_worker.html'

class ArticleWorkerShortageView(TemplateView):
    template_name = 'pages/article_worker_shortage.html'

class ArticleReduceCostView(TemplateView):
    template_name = 'pages/article_reduce_cost.html'

class ArticleSoloStabilityView(TemplateView):
    template_name = 'pages/article_solo_stability.html'

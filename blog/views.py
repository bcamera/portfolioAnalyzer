from django.shortcuts import render, get_object_or_404
from django.utils import timezone
from .models import Post
from .forms import PostForm
from django.shortcuts import redirect
from django.contrib import messages
import pandas as pd
import numpy as np

# A importação do Matplotlib deve ser feita após a definição do backend.
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from io import BytesIO
import PIL, PIL.Image
import yfinance as yf
from datetime import datetime
from django.http import HttpResponse

print_carteira_min_var = []

def home(request):
    return render(request, 'blog/index.html', {})

def carrega_dados(request, acao):
    agora = datetime.now()
    end = agora.strftime('%Y-%m-%d')
    start = '2018-01-01'
    
    acoes = [a.strip().upper() for a in acao.split(',')]
    lista_acoes_validas = []
    lista_inexistente = []
    lista_invalido = []

    for ticker in acoes:
        ticker_completo = ticker + '.SA'
        try:
            dados = yf.Ticker(ticker_completo).history(start=start, end=end)
            if not dados.empty and len(dados) >= 400:
                lista_acoes_validas.append(ticker_completo)
            elif not dados.empty:
                lista_invalido.append(ticker)
            else:
                lista_inexistente.append(ticker)
        except Exception:
            lista_inexistente.append(ticker)

    if not lista_acoes_validas:
        return HttpResponse("Nenhuma ação válida encontrada.", status=400)
    
    dados = yf.download(lista_acoes_validas, start=start, end=end)['Close']
    descreva = dados.describe()

    retorno_diario = dados.pct_change()
    retorno_anual = retorno_diario.mean() * 250

    cov_diaria = retorno_diario.cov()
    cov_anual = cov_diaria * 250
    retorno_carteira = []
    peso_acoes = []
    volatilidade_carteira = []
    sharpe_ratio = []
    numero_acoes = len(lista_acoes_validas)
    numero_carteiras = 10000
    np.random.seed(101)
    for cada_carteira in range(numero_carteiras):
        peso = np.random.random(numero_acoes)
        peso /= np.sum(peso)
        retorno = np.dot(peso, retorno_anual)
        volatilidade = np.sqrt(np.dot(peso.T, np.dot(cov_anual, peso)))
        sharpe = retorno / volatilidade
        sharpe_ratio.append(sharpe)
        retorno_carteira.append(retorno)
        volatilidade_carteira.append(volatilidade)
        peso_acoes.append(peso)

    carteira = {'Retorno': retorno_carteira,
                'Volatilidade': volatilidade_carteira,
                'Sharpe Ratio': sharpe_ratio}
    
    for contar,acao in enumerate(lista_acoes_validas):
        carteira[acao+' Peso'] = [Peso[contar] for Peso in peso_acoes]

    df = pd.DataFrame(carteira)

    colunas = ['Retorno', 'Volatilidade', 'Sharpe Ratio'] + [acao+' Peso' for acao in lista_acoes_validas]
    df = df[colunas]
    
    menor_volatilidade = df['Volatilidade'].min()
    maior_sharpe = df['Sharpe Ratio'].max()

    carteira_sharpe = df.loc[df['Sharpe Ratio'] == maior_sharpe]
    carteira_min_variancia = df.loc[df['Volatilidade'] == menor_volatilidade]

    fig, (ax1, ax2, ax3, ax4, ax5, ax6, ax7) = plt.subplots(nrows=7, ncols=1)
    plt.style.use('dark_background')
    
    ax2.plot(dados.index, dados.values)
    ax2.set_xlabel('Data')
    ax2.set_ylabel('Preco de Fechamento (R$)')
    ax2.legend(dados.columns)
    
    df.plot.scatter(x='Volatilidade', y='Retorno', c='Sharpe Ratio',
                    cmap='RdYlGn', edgecolors='black', figsize=(11, 18), grid=True, ax=ax4)
    ax4.scatter(x=carteira_sharpe['Volatilidade'], y=carteira_sharpe['Retorno'], c='red', marker='o', s=200)
    ax4.scatter(x=carteira_min_variancia['Volatilidade'], y=carteira_min_variancia['Retorno'], c='blue', marker='o', s=200)
    ax4.set_xlabel('Volatilidade')
    ax4.set_ylabel('Retorno Esperado')

    ax4.legend(loc='best', shadow=True, fontsize='x-large', labels=('Mínima Variância','Maior Retorno'))

    minimo = carteira_min_variancia['Retorno']
    minimo = minimo.tolist()
    risco = carteira_sharpe['Retorno']
    risco = risco.tolist()

    acaoMinRisc = []
    for j in lista_acoes_validas:
        acaoMinRisc.extend(carteira_min_variancia[j+' Peso'].tolist())
    map(float,acaoMinRisc)
    data2 = [round(k,4) for k in acaoMinRisc]
    data = [str(d) for d in data2]

    recipe = []
    for a,b in zip(acoes,data):
        recipe.append(a+' '+b)
        
    data = [float(x.split()[1]) for x in recipe]
    ingredients = [x.split()[0] for x in recipe]

    def func(pct, allvals):
        absolute = int(pct/100.*np.sum(allvals))
        return "{:.2f}%".format(pct, absolute)

    wedges, texts, autotexts = ax6.pie(data, autopct=lambda pct: func(pct, data),
                                        textprops=dict(color="w"))

    ax6.legend(wedges, ingredients,
                title="Ações",
                loc="center left",
                bbox_to_anchor=(1, 0, 0.5, 1))

    ax6.set_title("Mínima Variância")

    acaoMaiorRisc = []
    for j in lista_acoes_validas:
        acaoMaiorRisc.extend(carteira_sharpe[j+' Peso'].tolist())
    map(float,acaoMaiorRisc)
    data3 = [round(k,4) for k in acaoMaiorRisc]
    data4 = [str(d) for d in data3]

    recipe_Sharpe = []
    for a,b in zip(acoes,data4):
        recipe_Sharpe.append(a+' '+b)
        
    data4 = [float(x.split()[1]) for x in recipe_Sharpe]
    ingredients_sharpe = [x.split()[0] for x in recipe_Sharpe]

    def func(pct, allvals):
        absolute = int(pct/100.*np.sum(allvals))
        return "{:.2f}%".format(pct, absolute)

    wedges, texts, autotexts = ax7.pie(data4, autopct=lambda pct: func(pct, data4),
                                        textprops=dict(color="w"))
    ax7.legend(wedges, ingredients_sharpe,
                title="Ações",
                loc="center left",
                bbox_to_anchor=(1, 0, 0.5, 1))

    ax7.set_title("Maior Retorno")
    # =========================
    # Textos explicativos (com cor preta para aparecer no fundo branco)
    # =========================

    ax1.text(0.5, 1.0, 'Relatório da análise da carteira', size=24, ha='center', va='top', color='black')

    if (len(lista_inexistente) > 0) or (len(lista_invalido) > 0):
        ax1.text(0.0, 0.8, 'Os seguintes códigos foram removidos da análise:', 
                 size=10, color='red', ha='left', va='top')
        ax1.text(0.0, 0.7, 'Código(s) inválidos:'+str(lista_inexistente)[1:-1], 
                 size=10, color='red', ha='left', va='top')
        ax1.text(0.0, 0.6, 'Código(s) sem histórico suficiente:'+str(lista_invalido)[1:-1], 
                 size=10, color='red', ha='left', va='top')

    ax1.text(0.0, 0.5, 'A carteira a ser analisada é composta de '+str(len(lista_acoes_validas))+
             ' ações, sendo que durante o período analisado, podemos ver como cada ação se comportou ', 
             size=10, ha='left', va='top', color='black')
    ax1.text(0.0, 0.4, 'no gráfico logo abaixo :', size=10, ha='left', va='top', color='black')
    
    ax3.text(0.0, 0.5, 'Serão feitas duas análises utilizando o teorema do portfólio eficiente (links com mais informações no final da página)', 
             size=10, ha='left', va='top', color='black')
    ax3.text(0.0, 0.4, 'Na carteira de menor risco, o ponto azul no gráfico abaixo, tivemos um retorno anual de ' 
             + str(round(carteira_min_variancia['Retorno']*100,2)).split('\n',1)[0].split(' ',1)[1].strip()+'%.', 
             size=10, ha='left', va='top', color='black')
    ax3.text(0.0, 0.3, 'Já na carteira com o maior risco e retorno esperado, tivemos um retorno anual de ' 
             + str(round(carteira_sharpe['Retorno']*100,2)).split('\n',1)[0].split(' ',1)[1].strip()+
             '%, tomando como base o ponto', size=10, ha='left', va='top', color='black')
    ax3.text(0.0, 0.2, 'vermelho no gráfico abaixo.', size=10, ha='left', va='top', color='black')

    ax5.text(0.0, 0.5, 'Logo abaixo temos o peso de cada ação para os dois pontos no gráfico anterior, o primeiro sendo a carteira com menor variação pra quem quer menos risco.', 
             size=10, ha='left', va='top', color='black')
    ax5.text(0.0, 0.4, 'O segundo para os que não se importam muito com risco e preferem ter um maior retorno esperado.', 
             size=10, ha='left', va='top', color='black')

    # Mantém os eixos invisíveis mas permite texto
    ax1.axis("off")
    ax3.axis("off")
    ax5.axis("off")

    
    # Construa a imagem no buffer
    # buffer = BytesIO()
    # canvas = fig.canvas
    # canvas.draw()
    # pilImage = PIL.Image.frombytes("RGBA", canvas.get_width_height(), canvas.tostring_argb())
    # pilImage = pilImage.convert('RGB')
    # pilImage.save(buffer, "PNG")
    # plt.close(fig)

    # return HttpResponse(buffer.getvalue(), content_type="image/png")  

    # Ajusta layout para não cortar textos
    plt.tight_layout(rect=[0, 0, 1, 0.96])  # reserva 4% no topo para textos

    # Construa a imagem no buffer corretamente
    buffer = BytesIO()
    fig.savefig(buffer, format="png", dpi=150, bbox_inches="tight", pad_inches=0.5)
    plt.close(fig)
    buffer.seek(0)

    return HttpResponse(buffer.getvalue(), content_type="image/png")


    return HttpResponse(buffer.getvalue(), content_type="image/png")


def post_list(request):
    posts = Post.objects.filter(published_date__lte=timezone.now()).order_by('published_date')     
    return render(request, 'blog/post_list.html', {'posts': posts})
    
def post_detail(request, pk):
    post = get_object_or_404(Post, pk=pk)
    return render(request, 'blog/post_detail.html', {'post': post})
    
def post_new(request):
     if request.method == "POST":
         form = PostForm(request.POST)
         if form.is_valid():
             post = form.save(commit=False) 
             post.author = request.user
             post.published_date = timezone.now()
             post.save()
             return redirect('post_detail', pk=post.pk)
     else:
         form = PostForm()
     return render(request, 'blog/post_edit.html', {'form': form})    
     
def post_edit(request, pk):
     post = get_object_or_404(Post, pk=pk)
     if request.method == "POST":
         form = PostForm(request.POST, instance=post)
         if form.is_valid():
             post = form.save(commit=False)
             post.author = request.user
             post.published_date = timezone.now()
             post.save()
             return redirect('post_detail', pk=post.pk)
     else:
         form = PostForm(instance=post)
     return render(request, 'blog/post_edit.html', {'form': form})
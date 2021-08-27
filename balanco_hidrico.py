#!/usr/bin/env python

from tkinter import Tk, Label, Button, Entry, Checkbutton, IntVar
from tkinter.filedialog import askopenfilename, asksaveasfile
import geopandas
import fiona
from shapely.geometry import Point
from shapely.ops import cascaded_union
import pandas as pd
import numpy as np
from time import time
import matplotlib.pyplot as plt

fiona.supported_drivers['KML'] = 'rw'

from matplotlib import rcParams
rcParams.update({'figure.autolayout': True})

import ctypes
ctypes.windll.shcore.SetProcessDpiAwareness(1) #texto nitido em monitores de alta resolucao

kml_carregado = False

arquivo_bacias = "dados/bacias/Bacia_Hidrografica.shp"

dic_cod_bacia = {
    'gravataí': "dados/mini_bacias/G010_mini_19_02.shp",
    'sinos': "dados/mini_bacias/G020_mini_19_02.shp",
    'caí': "dados/mini_bacias/G030_mini_19_02.shp",
    'taquari-antas': "dados/mini_bacias/G040_mini_19_02.shp",
    'alto jacuí': "dados/mini_bacias/G050_mini_19_02.shp",
    'vacacaí-vacacaí-mirim': "dados/mini_bacias/G060_mini_19_02.shp",
    'baixo jacuí': "dados/mini_bacias/G070_mini_19_02.shp",
    'lago guaíba': "dados/mini_bacias/G080_mini_19_02.shp",
    'pardo': "dados/mini_bacias/G090_mini_19_02.shp",
    'tramandaí': "dados/mini_bacias/L010_mini_19_02.shp",
    'litoral médio': "dados/mini_bacias/L020_mini_19_02.shp",
    'camaquã': "dados/mini_bacias/L030_mini_19_02.shp",
    'mirim são gonçalo': "dados/mini_bacias/L040_mini_19_02.shp",
    'mampituba': "dados/mini_bacias/L050_mini_19_02.shp",
    'apuaê-inhandava': "dados/mini_bacias/U010_mini_19_02.shp",
    'passo fundo': "dados/mini_bacias/U020_min_19_02.shp",
    'turvo santa rosa santo cristo': "dados/mini_bacias/U030_mini_19_02.shp",
    'piratinim': "dados/mini_bacias/U040_mini_19_02.shp",
    'ibicuí': "dados/mini_bacias/U050_mini_19_02.shp",
    'quaraí': "dados/mini_bacias/U060_mini_19_02.shp",
    'santa maria': "dados/mini_bacias/U070_mini_19_02.shp",
    'negro': "dados/mini_bacias/U080_mini_19_02.shp",
    'ijuí': "dados/mini_bacias/U090_mini_19_02.shp",
    'várzea': "dados/mini_bacias/U100_mini_19_02.shp",
    'butuí-icamaquã': "dados/mini_bacias/U110_mini_19_02.shp",
}

print('Essa janela de terminal é aberta para mostrar a execução do software e possíveis erros.')
print('Envie qualquer mensagem de erro encontrada para roberto-rolo@sema.rs.gov.br.\n')

def selecionar_extrato():
    print('Lendo extrato do SIOUT...')
    extrato_siout = askopenfilename()
    print(extrato_siout)
    global df_extrato_siout
    df_extrato_siout = pd.read_csv(extrato_siout, sep=';', encoding='unicode_escape')
    print('Transformando as colunas de string para float...')
    colunas= ['Latitude', 'Longitude', 'Vazão janeiro', 'Vazão fevereiro', 'Vazão março', 'Vazão abril', 'Vazão maio', 'Vazão junho', 'Vazão julho', 'Vazão agosto', 'Vazão setembro', 'Vazão outubro', 'Vazão novembro', 'Vazão dezembro']
    for c in colunas:
        df_extrato_siout[c] = str_num_to_float(df_extrato_siout[c].values)
    print('Extrato do SIOUT lido com sucesso!\n')
    print('ATENÇÃO: o programa não faz nenhuma filtragem no extrato do SIOUT. Todos os cadastros listados serão levados em consideração no balanço hídrico!\n')
    btn_extrato["text"] = "extrato SIOUT carregado"

def selecionar_kml():
    print('Lendo kml da área de drenagem...')
    area_kml_str = askopenfilename()
    print(area_kml_str)
    global area_kml
    area_kml = geopandas.read_file(area_kml_str, driver='KML')
    print('Área de drenagem lida com sucesso!\n')
    global kml_carregado
    kml_carregado = True
    btn_kml["text"] = "kml carregado"

def remover_duplicatas(lista):
    s = []
    for i in lista:
        if i not in s:
            s.append(i)
    return s

def str_num_to_float(str_array):
    float_array = []
    for i in str_array:
        if i == '-':
            i = 0.
        else:
            i = str(i).replace(',', '.')
        float_array.append(float(i))
    return np.array(float_array)

def procurar_cadastros_siout(extrato, area):

    #processos do siout na area de drenagem
    print('Encontrando os processos do SIOUT que pertencem a área de drenagem...')
    t1 = time()

    xs = []
    ys = []
    ids = []
    for idx, row in extrato.iterrows():
        p = Point(row['Longitude'], row['Latitude'])
        if p.within(area[0]):
            xs.append(p.x)
            ys.append(p.y)
            ids.append(idx)

    t2 = time()
    delta_t = t2 - t1
    print('Isso levou {} segundos \n'.format(int(delta_t)))

    return xs, ys, ids

def calcular():
    print('Calculando balanço hídrico...\n')

    print('Lendo arquivo das bacias hidrográficas...\n')
    bacias = geopandas.read_file(arquivo_bacias)
    #bacias = bacias.to_crs("EPSG:4674")

    print('Lendo coordenadas...')
    longitude =  float(entry_x.get().replace(',','.'))
    latitude =  float(entry_y.get().replace(',','.'))
    ponto_informado = Point((longitude, latitude))
    print('O ponto informado é: {}\n'.format(ponto_informado))

    print('Verificando a qual bacia o ponto informado petence...')
    pertence = False
    for idx, row in bacias.iterrows():
        if ponto_informado.within(row['geometry']):
            bacia = row['nome']
            bacia_idx = idx
            print('O ponto selcionado pertence a bacia {}\n'.format(bacia))
            pertence = True
            break

    if pertence == True:

        print('Lendo arquivo de mini bacias...')
        t1 = time()
        mini_bacias = geopandas.read_file(dic_cod_bacia[bacia.lower()])
        #mini_bacias = mini_bacias.to_crs("EPSG:4674")
        t2 = time()
        delta_t = t2 - t1
        print('Isso levou {} segundos \n'.format(int(delta_t)))
        

        print('Verificando a qual mini bacia o ponto informado petence...')
        t1 = time()
        for idx, row in mini_bacias.iterrows():
            if ponto_informado.within(row['geometry']):
                mini_bacia = row['Mini']
                mini_bacia_idxs = idx
                print('O ponto selcionado pertence a mini bacia {}'.format(mini_bacia))
                t2 = time()
                delta_t = t2 - t1
                print('Isso levou {} segundos \n'.format(int(delta_t)))
                break

        if kml_carregado == False:

            print('Encontrando as mini bacias que pertencem a área de drenagem...')
            print('Há {} mini bacias.'.format(len(mini_bacias)))
            t1 = time()
            c = 1
            ad_c = [mini_bacia]

            minis = mini_bacias['Mini'].values
            minijus = mini_bacias['MiniJus']
            indices = mini_bacias.index.values
            filtro = np.zeros(len(minis))
            filtro[mini_bacia_idxs] = 1

            existe_bacia = True
            while existe_bacia == True:
                print('Iteração {} para {} mini bacias'.format(c, len(ad_c)))
                ad_p = []
                for mb in ad_c:
                    f = minijus == mb
                    filtro[f] = 1
                    ad_p = ad_p + minis[f].tolist()
                if len(ad_c) == 0:
                    existe_bacia = False
                else:
                    ad_c = remover_duplicatas(ad_p)
                    c = c + 1

            print('{} mini bacias fazem parte da área de drenagem.'.format(sum(filtro)))
            ad_idx = indices[np.where(filtro == 0, False, True)]
            t2 = time()
            delta_t = t2 - t1
            print('Isso levou {} segundos \n'.format(int(delta_t)))

            print('Aglutinando as minibacias...')
            t1 = time()
            polys = [mini_bacias.iloc[idx]['geometry'] for idx in ad_idx]
            mini_bacias_uniao = geopandas.GeoSeries(cascaded_union(polys))
            t2 = time()
            delta_t = t2 - t1
            print('Isso levou {} segundos \n'.format(int(delta_t)))

            if kml_b.get() == 1:
                arquivo_kml = asksaveasfile(defaultextension=".kml")
                mini_bacias_uniao.to_file(arquivo_kml.name, driver='KML')

        else:

            mini_bacias_uniao = area_kml.loc[[0], 'geometry']

        xs, ys, ids = procurar_cadastros_siout(df_extrato_siout, mini_bacias_uniao)

        #Plotando os mapas
        print('Plotando...')
        fig, ax = plt.subplots(figsize=(8,8))

        bacias.loc[[bacia_idx], 'geometry'].plot(ax=ax, color='gainsboro', edgecolor='silver', alpha=1)
        mini_bacias_uniao.plot(ax=ax, color='gray', alpha=1)
        mini_bacias.loc[[mini_bacia_idxs], 'geometry'].plot(ax=ax, color='black', alpha=1)
        ax.scatter(ponto_informado.x, ponto_informado.y, label='Ponto informado', marker='x', s=50)
        if len(xs) > 0:
            ax.scatter(x=xs, y=ys, label='Cadastros SIOUT')
        
        plt.title('Bacia {}'.format(bacia))
        plt.ylabel('Latitude')
        plt.xlabel('Longitude')
        plt.legend()
        plt.grid()

        plt.tight_layout()
        #manager = plt.get_current_fig_manager()
        #manager.full_screen_toggle()
        plt.show()

        #plotando o balanço hídrico
        vaz_simulada = float(entry_vs.get().replace(',','.'))
        vaz_bacias = mini_bacias.loc[mini_bacia_idxs, ['Qref01', 'Qref02', 'Qref03', 'Qref04', 'Qref05', 'Qref06', 'Qref07', 'Qref08', 'Qref09', 'Qref10', 'Qref11', 'Qref12']].values
        vaz_siout = df_extrato_siout.loc[ids, ['Vazão janeiro', 'Vazão fevereiro', 'Vazão março', 'Vazão abril', 'Vazão maio', 'Vazão junho', 'Vazão julho', 'Vazão agosto', 'Vazão setembro', 'Vazão outubro', 'Vazão novembro', 'Vazão dezembro']]
        vaz_siout_mes = np.sum(vaz_siout, axis=0).values

        print('PROPRIEDADES:')
        perc_out =  mini_bacias.loc[mini_bacia_idxs, 'perc_out']
        print('Máximo outorgável: {}'.format(perc_out))
        vaz_max_out = vaz_bacias * perc_out
        bal_inicial = vaz_max_out - vaz_siout_mes
        bal_final = bal_inicial - vaz_simulada

        print('Vazão da bacia: {}'.format(vaz_bacias))
        print('Usos SIOUT: {}'.format(vaz_siout_mes))
        print('Balanço inicial: {}'.format(bal_inicial))
        print('Balanço final: {}'.format(bal_final))

        area_de_drenagem = mini_bacias.loc[mini_bacia_idxs, 'AreaDren']
        print('Área de drenagem: {}'.format(area_de_drenagem))
        #print('Vazão de referência: {}'.format('N/D'))

        tick_label = ['jan', 'fev', 'mar', 'abr', 'mai', 'jun', 'jul', 'ago', 'set', 'out', 'nov', 'dez']

        fig, axs = plt.subplots(2, 1, figsize=(15,8))

        cores = np.where(bal_inicial > 0, 'g', 'r')
        axs[0].bar([x for x in range(1, 13)], bal_inicial, tick_label=tick_label, color=cores)
        for x,y in zip([x for x in range(1, 13)], bal_inicial):
            axs[0].text(x-.25, y, str(round(y,4)))
        axs[0].set_title('Balanço inicial')
        axs[0].set_ylabel('Vazão m³/s')
        axs[0].grid()
        cores = np.where(bal_final > 0, 'g', 'r')
        axs[1].bar([x for x in range(1, 13)], bal_final, tick_label=tick_label, color=cores)
        for x,y in zip([x for x in range(1, 13)], bal_final):
            axs[1].text(x-.25, y, str(round(y,4)))
        axs[1].set_title('Balanço final')
        axs[1].set_ylabel('Vazão m³/s')
        axs[1].grid()

        plt.tight_layout()
        #manager = plt.get_current_fig_manager()
        #manager.full_screen_toggle()
        plt.show()

    else:
        print('O ponto não pertence ao estado do RS.')

#GUI
root = Tk()
root.title("Balanço hídrico")
root.resizable(False, False)

label_y = Label(root, text="Latitude:")
label_y.grid(row=0, column=0, sticky='W', padx=10, pady=10)

label_x = Label(root, text="Longitude:")
label_x.grid(row=1, column=0, sticky='W', padx=10, pady=10)

entry_y = Entry(root, width=8)
entry_y.grid(row=0, column=1, sticky='E', padx=10, pady=10)

entry_x = Entry(root, width=8)
entry_x.grid(row=1, column=1, sticky='E', padx=10, pady=10)

label_vs = Label(root, text="Vazão simulada:")
label_vs.grid(row=2, column=0, sticky='W', padx=10, pady=10)

entry_vs = Entry(root, width=8)
entry_vs.grid(row=2, column=1, sticky='E', padx=10, pady=10)

btn_extrato = Button(root, text="Selecione o extrato do SIOUT", command=selecionar_extrato)
btn_extrato.grid(row=3, column=0, sticky='W', padx=10, pady=10)

kml_b = IntVar()
salvar_kml = Checkbutton(root, variable=kml_b, onvalue=1, offvalue=0, text='Salvar KML')
salvar_kml.grid(row=4, column=0, sticky='W', padx=10, pady=10)

#btn_kml = Button(root, text="Carregar área de drenagem", command=selecionar_kml)
#btn_kml.grid(row=5, column=0, sticky='W', padx=10, pady=10)

btn_calcular = Button(root, text="Calcular balanço hídrico", command=calcular)
btn_calcular.grid(row=5, column=1, sticky='E', padx=10, pady=10)

root.mainloop()

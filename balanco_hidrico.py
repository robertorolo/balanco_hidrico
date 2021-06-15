#!/usr/bin/env python

from tkinter import Tk, Label, Button, Entry
from tkinter.filedialog import askopenfilename
import geopandas
from shapely.geometry import Point
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

arquivo_bacias = "dados/Bacia_Hidrografica/Bacia_Hidrografica.shp"

dic_cod_bacia = {
    'gravataí': "dados/G010/G010_mini_19_02.shp",
}

print('Essa janela de terminal é aberta para mostrar possíveis erros.\n')

def str_num_to_float(str_array):
    float_array = []
    for i in str_array:
        if i == '-':
            i = 0.
        else:
            i = str(i).replace(',', '.')
        float_array.append(float(i))
    return np.array(float_array)

def calcular():
    print('Calculando balanço hídrico...\n')
    
    print('Lendo arquivo das bacias hidrográficas...\n')
    bacias = geopandas.read_file(arquivo_bacias)
    bacias = bacias.to_crs("EPSG:4674")
    
    print('Lendo coordenadas...')
    longitude =  float(entry_x.get().replace(',','.'))
    latitude =  float(entry_y.get().replace(',','.'))
    ponto_informado = Point((longitude, latitude))
    print('O ponto informado é: {}\n'.format(ponto_informado))

    print('Verificando a qual bacia o ponto informado petence...')
    for idx, row in bacias.iterrows():
        if ponto_informado.within(row['geometry']):
            bacia = row['nome']
            bacia_idx = idx
            break
    print('O ponto selcionado pertence a bacia {}\n'.format(bacia))

    print('Lendo arquivo de mini bacias...\n')
    mini_bacias = geopandas.read_file(dic_cod_bacia[bacia.lower()])
    mini_bacias = mini_bacias.to_crs("EPSG:4674")

    
    print('Verificando a qual mini bacia o ponto informado petence...')
    for idx, row in mini_bacias.iterrows():
        if ponto_informado.within(row['geometry']):
            mini_bacia = int(row['Mini'])
            mini_bacia_idxs = idx
            print('O ponto selcionado pertence a mini bacia {}\n'.format(mini_bacia))
            break

    print('Encontrando as mini bacias que pertencem a área de drenagem...')
    ad = [mini_bacia]
    ad_idx = [mini_bacia_idxs]
    ad_c = ad.copy()
    
    existe_bacia = True
    while existe_bacia == True:
        ad_p = []
        for mb in ad_c:
            for idx, row in mini_bacias.iterrows():
                if row['MiniJus'] == mb:
                    ad_p.append(int(row['Mini']))
                    ad_idx.append(idx)
        if len(ad_p) == 0:
            existe_bacia = False
        else:
            ad = ad + ad_p
            ad_c = ad_p.copy()

    #removendo a minibacia original
    bd_i = ad_idx[0]
    ad = ad[1:]
    ad_idx = ad_idx[1:]
    
    print('As mini bacias que pertencem a area de drenagem são {}\n'.format(ad))

    print('Encontrando os processos do SIOUT que pertencem a área de drenagem...\n')
    xs = []
    ys = []
    ids = []
    for idx, row in df_extrato_siout.iterrows():
        p = Point(row['Longitude'], row['Latitude'])
        for b_idx in ad_idx: 
            if p.within(mini_bacias.loc[b_idx, 'geometry']):
                xs.append(p.x)
                ys.append(p.y)
                ids.append(idx)

    #Plotando os mapas
    fig, ax = plt.subplots(figsize=(12,12))
    bacias.loc[[bacia_idx], 'geometry'].plot(ax=ax, color='gainsboro', edgecolor='silver', alpha=1)
    mini_bacias.loc[ad_idx, 'geometry'].plot(ax=ax, color='gray', alpha=1)
    mini_bacias.loc[[bd_i], 'geometry'].plot(ax=ax, color='green', alpha=1)
    ax.scatter(x=xs, y=ys, label='Cadastros SIOUT')

    ax.scatter(ponto_informado.x, ponto_informado.y, label='Ponto informado', marker='x', s=50)

    plt.title('Bacia {}'.format(bacia))
    plt.ylabel('Latitude')
    plt.xlabel('Longitude')
    plt.legend()
    plt.grid()
    
    plt.tight_layout()
    plt.show()

    print('Feche a janela do mapa para mostrtar o próximo gráfico.')

    #plotando o balanço hídrico
    vaz_bacias = mini_bacias.loc[ad_idx, ['Qref01', 'Qref02', 'Qref03', 'Qref04', 'Qref05', 'Qref06', 'Qref07', 'Qref08', 'Qref09', 'Qref10', 'Qref11', 'Qref12']]
    vaz_siout = df_extrato_siout.loc[ids, ['Vazão janeiro', 'Vazão fevereiro', 'Vazão março', 'Vazão abril', 'Vazão maio', 'Vazão junho', 'Vazão julho', 'Vazão agosto', 'Vazão setembro', 'Vazão outubro', 'Vazão novembro', 'Vazão dezembro']]

    vaz_bacias_mes = np.sum(vaz_bacias, axis=0).values
    vaz_siout_mes = np.sum(vaz_siout, axis=0).values

    area_de_drenagem = np.sum(mini_bacias.loc[ad_idx, 'AreaMini'])
    print('Área de drenagem: {}'.format(area_de_drenagem))

    tick_label = ['jan', 'fev', 'mar', 'abr', 'mai', 'jun', 'jul', 'ago', 'set', 'out', 'nov', 'dez']

    if np.sum(vaz_siout_mes) == 0:
        fig, ax = plt.subplots(figsize=(12,12))

        ax.bar([x for x in range(1, 13)], vaz_bacias_mes, tick_label=tick_label)
        ax.set_ylabel('Balanço inicial')

        plt.show()
    else:
        fig, axs = plt.subplots(2, 1, figsize=(12,12))

        axs[0].bar([x for x in range(1, 13)], vaz_bacias_mes, tick_label=tick_label)
        axs[0].set_ylabel('Balanço inicial')
        axs[1].bar([x for x in range(1, 13)], (vaz_bacias_mes-vaz_siout_mes), tick_label=tick_label)
        axs[1].set_ylabel('Balanço final')

        plt.show()

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

btn_extrato = Button(root, text="Selecione o extrato do SIOUT", command=selecionar_extrato)
btn_extrato.grid(row=2, column=0, sticky='W', padx=10, pady=10)

btn_calcular = Button(root, text="Calcular balanço hídrico", command=calcular)
btn_calcular.grid(row=3, column=1, sticky='E', padx=10, pady=10)

root.mainloop()
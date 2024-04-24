import tkinter as tk
from tkinter import ttk,messagebox
import requests 
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
from tkcalendar import DateEntry
from datetime import date
import re


# FUNCIÓN PRINCIPAL
def main():
    # Configuración de la aplicación principal
    root = tk.Tk()
    root.title("Aplicación de Datos COVID-19")

    url_label = ttk.Label(root, text="Introduce la URL a continuación:")
    url_label.pack(pady=10)

    url_entry = ttk.Entry(width=47)
    url_entry.pack(pady=10)

    endpoint_label = ttk.Label(root, text="Endpoint:")
    endpoint_label.pack(pady=10)

    # Creación del ComboBox para selección de endpoint
    # Definir los endpoints disponibles
    endpoints = ['reports', 'regions']
    endpoint_combobox = ttk.Combobox(root, values=endpoints, width=47, state='readonly')
    endpoint_combobox.pack(pady=10)
    endpoint_combobox.set('reports')  # Valor por defecto

    # Configuración de selección de fecha
    date_label = ttk.Label(root, text="Fecha:")
    date_label.pack(pady=10)

    dt1 = date(2020, 1, 22)  # Fecha mínima para selección
    dt2 = date(2022, 12, 31)  # Fecha máxima para selección

    cal = DateEntry(root, width=12, background='darkblue',
                    foreground='white', borderwidth=2,
                    year=2022, mindate=dt1, maxdate=dt2, date_pattern="yyyy-mm-dd")
    cal.pack(pady=20, padx=20)

    # Botón para obtener datos
    global fetch_button,deaths_button,infected_button,MostDeath_button,MostInfected_button,regions_button
    fetch_button = ttk.Button(root, text="Obtener Datos", command=lambda: fetch_data(url_entry.get(), endpoint_combobox, cal))
    fetch_button.pack(pady=20)

    # Botones para mostrar datos
    deaths_button = ttk.Button(root, text="Mostrar Total de Muertes", command=lambda: show_TotalDeathsByDate(datos),state='disabled')
    deaths_button.pack(pady=20, padx=20)

    infected_button = ttk.Button(root, text="Mostrar Total de Infectados", command=lambda: show_TotalInfectedByDate(datos),state='disabled')
    infected_button.pack(pady=20, padx=20)

    MostDeath_Label = ttk.Label(root, text="Muertos > 10000")
    MostDeath_Label.pack(pady=3)

    MostDeath_button = ttk.Button(root, text="Mostrar países con más muertes", command=lambda: show_MostDeathByDate(datos),state='disabled')
    MostDeath_button.pack(pady=20, padx=20)

    MostInfected_Label = ttk.Label(root, text="Infectados > 1000000")
    MostInfected_Label.pack(pady=3)

    MostInfected_button = ttk.Button(root, text="Mostrar países con más infectados", command=lambda: show_MostInfectedByDate(datos),state='disabled')
    MostInfected_button.pack(pady=20, padx=20)

    regions_button = ttk.Button(root, text="Mostrar Todas las Regiones", command=lambda: show_AllRegions(root, datos),state='disabled')
    regions_button.pack(pady=20, padx=20)

    # Marco para la gestión del grid
    grid_wnd = tk.Tk()
    grid_wnd.title("Aplicación de Datos COVID-19")

    # Crear un widget Treeview
    global treeres
    treeres = ttk.Treeview(grid_wnd, columns=('Data1', 'Data2'), show='headings')
    treeres.grid(row=1, column=0, columnspan=3, padx=10, pady=10, sticky='nsew')

    # Definir los encabezados de las columnas
    treeres.heading('Data1', text='Dato')
    treeres.heading('Data2', text='Resultado')

    # Ejecución del bucle principal
    root.mainloop()

# Función para obtener datos
def fetch_data(url, endpoint_combobox, cal):
    messagebox.showinfo("Mensaje", "Cargando datos, por favor espere")
    base_url = url
    endpoint = endpoint_combobox.get()
    url = f"{base_url}{endpoint}"
    params = {
        "date": cal.get_date().strftime('%Y-%m-%d')  # Ajusta los parámetros según la API
    }
    
    data = get_covid_data(url, params)
    if (data):
        global datos
        df = pd.json_normalize(data)
        datos = df
        messagebox.showinfo("Mensaje", "Datos cargados con éxito")
        fetch_button.configure(state='enable')
        deaths_button.configure(state='enable')
        infected_button.configure(state='enable')
        MostDeath_button.configure(state='enable')
        MostInfected_button.configure(state='enable')
        regions_button.configure(state='enable')
    else:
        messagebox.showinfo("Mensaje", "No fue posible cargar los datos")

# Función para obtener datos de la API
def get_covid_data(url, params):
    # Validación de la URL
    if not re.match(r'https?://[^\s]+', url):  # regex simple para verificar una URL válida
        messagebox.showinfo("Mensaje", "La URL proporcionada no es válida.")
        return None
    
    # Estableciendo un tiempo de espera para la solicitud
    timeout_duration = 10  # tiempo de espera después de 10 segundos

    try:
        # Usando requests para obtener los datos con tiempo de espera
        response = requests.get(url, params=params, timeout=timeout_duration)
        
        # Verificando la respuesta
        if response.status_code == 200:
            data = response.json().get('data')
            if data is not None:
                return data
            else:
                messagebox.showinfo("Mensaje", "La respuesta de la API no contiene 'data'.")
                return None
        else:
            messagebox.showinfo("Mensaje", "No fue posible cargar los datos, Error: " + str(response.status_code))
            return None
    except requests.ConnectionError:
        messagebox.showinfo("Mensaje", "Error de conexión al servidor.")
        return None
    except requests.Timeout:
        messagebox.showinfo("Mensaje", "Tiempo de espera agotado para la solicitud.")
        return None
    except Exception as e:
        messagebox.showinfo("Mensaje", "No fue posible cargar los datos, Error: " + str(e))
        return None
    
# Función para mostrar el total de muertes por fecha
def show_TotalDeathsByDate(df):
    try:
        # Filtrar los datos para mostrar solo las muertes por país
        deaths_df = df[['region.name', 'deaths']].groupby('region.name').sum().reset_index()
        print(deaths_df)

        # Cargar el archivo shapefile del mapa mundial
        world = gpd.read_file(gpd.datasets.get_path('naturalearth_lowres'))

        # Unir los datos de muertes con el shapefile del mapa mundial
        world = world.merge(deaths_df, how='left', left_on=['name'], right_on=['region.name'])
        
        # Visualizar las muertes por COVID-19 en un mapa mundial
        fig, ax = plt.subplots(1, 1, figsize=(15, 8))
        world.plot(column='deaths', cmap='Reds', linewidth=0.8, ax=ax, edgecolor='0.8', legend=True)
        for idx, row in world.iterrows():
            plt.annotate(text=row['name'], xy=(row['geometry'].centroid.x, row['geometry'].centroid.y), horizontalalignment='center')

        ax.set_title('Total de muertes por COVID-19 por país')
        ax.axis('off')

        # Limpia la lista anterior en el widget Treeview
        for item in treeres.get_children():
            treeres.delete(item)
        treeres.insert('', 'end', values=("Desviación estándar muestral", str(deaths_df['deaths'].std())))
        treeres.insert('', 'end', values=("Media", str(deaths_df['deaths'].mean())))
        treeres.insert('', 'end', values=("Mediana", str(deaths_df['deaths'].median())))
        plt.show()

    except Exception as e:
        messagebox.showinfo("Mensaje", "Debe cargar primero los datos de 'reports'")

# Función para mostrar el total de infectados por fecha
def show_TotalInfectedByDate(df):
    try:
        # Filtrar los datos para mostrar solo los infectados por país
        infected_df = df[['region.name', 'confirmed']].groupby('region.name').sum().reset_index()
        print(infected_df)

        # Cargar el archivo shapefile del mapa mundial
        world = gpd.read_file(gpd.datasets.get_path('naturalearth_lowres'))

        # Unir los datos de infectados con el shapefile del mapa mundial
        world = world.merge(infected_df, how='left', left_on=['name'], right_on=['region.name'])
        
        # Visualizar los infectados por COVID-19 en un mapa mundial
        fig, ax = plt.subplots(1, 1, figsize=(15, 8))
        world.plot(column='confirmed', cmap='Greens', linewidth=0.8, ax=ax, edgecolor='0.8', legend=True)
        for idx, row in world.iterrows():
            plt.annotate(text=row['name'], xy=(row['geometry'].centroid.x, row['geometry'].centroid.y), horizontalalignment='center')

        ax.set_title('Total de infectados por COVID-19 por país')
        ax.axis('off')

        # Limpia la lista anterior en el widget Treeview
        for item in treeres.get_children():
            treeres.delete(item)
        treeres.insert('', 'end', values=("Desviación estándar muestral", str(infected_df['confirmed'].std())))
        treeres.insert('', 'end', values=("Media", str(infected_df['confirmed'].mean())))
        treeres.insert('', 'end', values=("Mediana", str(infected_df['confirmed'].median())))

        plt.show()
    except Exception as e:
        messagebox.showinfo("Mensaje", "Debe cargar primero los datos de 'reports'")

# Función para mostrar países con más muertes
def show_MostDeathByDate(df):
    try:
        # Filtrar los datos para mostrar solo las muertes por país
        deaths_df = df[['region.name', 'deaths']].groupby('region.name').sum().reset_index()
        print(deaths_df)
        # Filtrar por más de 100000 muertes
        significant_deaths = deaths_df.loc[deaths_df['deaths'] > 10000]

        ## Cargar el archivo shapefile del mapa mundial
        #world = gpd.read_file(gpd.datasets.get_path('naturalearth_lowres'))
#
        ## Unir los datos de muertes significativas con el shapefile del mapa mundial
        #world = world.merge(significant_deaths, how='left', left_on=['name'], right_on=['region.name'])
        #
        ## Visualizar las muertes por COVID-19 en un mapa mundial para países con más de 100000 muertes
        #fig, ax = plt.subplots(1, 1, figsize=(15, 8))
        #world.plot(column='deaths', cmap='Reds', linewidth=0.8, ax=ax, edgecolor='0.8', legend=True)
        #for idx, row in world.iterrows():
        #    plt.annotate(text=row['name'], xy=(row['geometry'].centroid.x, row['geometry'].centroid.y), horizontalalignment='center')
#
        #ax.set_title('Países con más de 100000 muertes')
        #ax.axis('off')

        # Limpia la lista anterior en el widget Treeview
        for item in treeres.get_children():
            treeres.delete(item)
        treeres.insert('', 'end', values=("Desviación estándar muestral", str(significant_deaths['deaths'].std())))
        treeres.insert('', 'end', values=("Media", str(significant_deaths['deaths'].mean())))
        treeres.insert('', 'end', values=("Mediana", str(significant_deaths['deaths'].median())))

        # Mostrar los muertos por país en un gráfico de barras
        significant_deaths.plot(kind='barh', x='region.name', y='deaths', figsize=(15, 8),color='red')
        plt.title('Muertes por COVID-19 por país')
        plt.xlabel('País')
        plt.ylabel('Muertes')
        plt.show()

    except Exception as e:
        messagebox.showinfo("Mensaje", "Aún los datos no se encuentran en el rango adecuado")
        plt.close('all')

# Función para mostrar países con más infectados
def show_MostInfectedByDate(df):
    try:
        # Filtrar los datos para mostrar solo los infectados por país
        infected_df = df[['region.name', 'confirmed']].groupby('region.name').sum().reset_index()
        print(infected_df)
        # Filtrar por más de 1000000 de infectados
        significant_infections = infected_df.loc[infected_df['confirmed'] > 1000000]
        print(significant_infections)

        ## Cargar el archivo shapefile del mapa mundial
        #world = gpd.read_file(gpd.datasets.get_path('naturalearth_lowres'))
#
        ## Unir los datos de infectados significativos con el shapefile del mapa mundial
        #world = world.merge(significant_infections, how='left', left_on=['name'], right_on=['region.name'])
        #
        ## Visualizar los infectados por COVID-19 en un mapa mundial para países con más de 1000000 de infectados
        #fig, ax = plt.subplots(1, 1, figsize=(15, 8))
        #world.plot(column='confirmed', cmap='Greens', linewidth=0.8, ax=ax, edgecolor='0.8', legend=True)
        #for idx, row in world.iterrows():
        #    plt.annotate(text=row['name'], xy=(row['geometry'].centroid.x, row['geometry'].centroid.y), horizontalalignment='center')
#
        #ax.set_title('Países con más de 1000000 de infectados')
        #ax.axis('off')

        # Limpia la lista anterior en el widget Treeview
        for item in treeres.get_children():
            treeres.delete(item)
        treeres.insert('', 'end', values=("Desviación estándar muestral", str(significant_infections['confirmed'].std())))
        treeres.insert('', 'end', values=("Media", str(significant_infections['confirmed'].mean())))
        treeres.insert('', 'end', values=("Mediana", str(significant_infections['confirmed'].median())))

        # Mostrar los infectados por país en un gráfico de barras
        significant_infections.plot(kind='barh', x='region.name', y='confirmed', figsize=(15, 8), color='green')
        plt.title('Infectados por COVID-19 por país')
        plt.xlabel('País')
        plt.ylabel('Infectados')
        plt.show()

    except Exception as e:
        messagebox.showinfo("Mensaje", "Aún los datos no se encuentran en el rango adecuado")
        plt.close('all')

# Función para mostrar todas las regiones
def show_AllRegions(root, df):
    try:
        regions_button.config(state='disable')
        sorted_df = df.sort_values(by='name', ascending=True)

        # Crear un marco para sostener el widget Treeview y una posible barra de desplazamiento
        frame = tk.Frame(root)
        frame.pack(fill=tk.BOTH, expand=True)

        # Crear el widget Treeview
        tree = ttk.Treeview(frame, columns=list(sorted_df.columns), show='headings')
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Agregar una barra de desplazamiento vertical
        scrollbar = ttk.Scrollbar(frame, orient='vertical', command=tree.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        tree.configure(yscrollcommand=scrollbar.set)

        # Definir los encabezados de las columnas
        for col in sorted_df.columns:
            tree.heading(col, text=col)
            tree.column(col, width=tk.font.Font().measure(col.title()))

        # Insertar datos en el widget Treeview
        for index, row in sorted_df.iterrows():
            tree.insert("", tk.END, values=list(row))
    except Exception as e:
        regions_button.config(state='enable')
        messagebox.showinfo("Mensaje", "Debe cargar primero los datos de 'regions'")

main()
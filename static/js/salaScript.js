// Usamos los nombres definidos en el importmap de base.html
import React from "react";
import { createRoot } from "react-dom/client";
import { Excalidraw } from "@excalidraw/excalidraw";

const App = () => {
    // Estado simple para controlar la API si la necesitas luego
    const [excalidrawAPI, setExcalidrawAPI] = React.useState(null);

    return React.createElement(
        React.Fragment,
        null,
        React.createElement(
            "div",
            {
                // Es vital que este contenedor tenga altura (100% del padre)
                style: { height: "100%", width: "100%" } 
            },
            React.createElement(Excalidraw, {
                langCode: "es-ES",
                excalidrawAPI: (api) => setExcalidrawAPI(api),
                // Opcional: Opciones de inicialización
                initialData: {
                    appState: { viewBackgroundColor: "#ffffff" },
                },
            })
        )
    );
};

// Montar la aplicación
const container = document.getElementById("app");
if (container) {
    const root = createRoot(container);
    root.render(React.createElement(App));
} else {
    console.error("No se encontró el elemento #app para montar Excalidraw");
}
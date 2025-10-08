import React from "react";
import { AppMemoryProvider } from "../memory/app_memory";
import { DataMemoryProvider } from "../memory/data_memory";
import { SearchMemoryProvider } from "../memory/search_memory";
import { UIMemoryProvider } from "../memory/ui_memory";
import { ChatbotMemoryProvider } from "../memory/chatbot_memory";
import ActionBusHandler from "../components/ActionBusHandler";
import AppRouter from "./AppRouter";
import "../css_design/styles/globals.css";

//nesting is done here such that the inner most approuter can get access data components

function App() {
  return (
    <UIMemoryProvider>
      <DataMemoryProvider>
        <SearchMemoryProvider>
          <AppMemoryProvider>
            <ChatbotMemoryProvider>
              <ActionBusHandler />
              <AppRouter />
            </ChatbotMemoryProvider>
          </AppMemoryProvider>
        </SearchMemoryProvider>
      </DataMemoryProvider>
    </UIMemoryProvider>
  );
}

export default App;

import * as React from "react"
import { cn } from "@/lib/utils"

// Simple chart context
const ChartContext = React.createContext<{ config: Record<string, any> }>({
  config: {},
})

interface ChartContainerProps extends React.HTMLAttributes<HTMLDivElement> {
  config: Record<string, any>
  children: React.ComponentProps<"div">["children"]
}

const ChartContainer = React.forwardRef<HTMLDivElement, ChartContainerProps>(
  ({ className, config, children, ...props }, ref) => {
    return (
      <ChartContext.Provider value={{ config }}>
        <div
          ref={ref}
          className={cn("w-full h-full", className)}
          {...props}
        >
          {children}
        </div>
      </ChartContext.Provider>
    )
  }
)
ChartContainer.displayName = "ChartContainer"

export { ChartContainer }
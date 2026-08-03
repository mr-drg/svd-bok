import { componentRegistry } from "./quartz/components/registry"
import { loadQuartzConfig, loadQuartzLayout } from "./quartz/plugins/loader/config-loader"

// og-image plugin's readingTimeText is a function, so it can't be set via
// quartz.config.yaml — override it here to localize "N min read" -> RU.
componentRegistry.setOptionOverrides("@quartz-community/og-image", {
  readingTimeText: (minutes: number) => `${minutes} мин. чтения`,
})

const config = await loadQuartzConfig()
export default config
export const layout = await loadQuartzLayout()

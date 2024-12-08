#!/usr/bin/env Rscript

# Only run install.packages() if you need to install the packages.
# Otherwise, comment these out if packages are already installed.
# options(repos = c(CRAN = "https://cloud.r-project.org/"))
# install.packages("ggplot2")
# install.packages("dplyr")
# install.packages("tidyr")
# install.packages("readr")

library(ggplot2)
library(dplyr)
library(tidyr)
library(readr)

cat("Enter a two-letter state code (e.g. 'NY', 'CA', 'DC', or 'ALL'): ")
selected_state <- readLines(con="stdin", n=1)
selected_state <- toupper(selected_state)

allsubmissions_path <- paste0("../results/data/", selected_state, "_SubmissionsEnrichedExpanded.csv")
uniquesubmissions_path <- paste0("../results/data/", selected_state, "_UniqueComplaintsEnrichedExpanded.csv")

if (!file.exists(allsubmissions_path) || !file.exists(uniquesubmissions_path)) {
  stop("Data files not found for the selected state.")
}

allsubmissions <- read.csv(allsubmissions_path)
uniquesubmissions <- read.csv(uniquesubmissions_path)

# Calculate required metrics once
unique_submission_count <- nrow(uniquesubmissions %>% distinct(Remedy.Case.Number))
all_submission_count <- nrow(allsubmissions)
rejected_submission_count <- sum(uniquesubmissions$Total.number.of.rejections.associated.with.this.CASENBR, na.rm = TRUE)
average_rejections <- uniquesubmissions %>%
  summarize(avg_rejections = mean(Total.number.of.rejections.associated.with.this.CASENBR, na.rm = TRUE))
max_rejections <- uniquesubmissions %>%
  summarize(max_rejections = max(Total.number.of.rejections.associated.with.this.CASENBR, na.rm = TRUE))

rejections_only <- uniquesubmissions %>%
  filter(Total.number.of.submissions.associated.with.this.CASENBR == Total.number.of.rejections.associated.with.this.CASENBR)
rejections_only_count <- nrow(rejections_only)
percentage_rejection_only <- (rejections_only_count / unique_submission_count) * 100
rej_only_average_rejections <- rejections_only %>%
  summarize(rej_only_avg = mean(Total.number.of.rejections.associated.with.this.CASENBR, na.rm = TRUE))

# Print some basic info
cat("Number of submissions:", all_submission_count, "\n")
cat("Number of rejected submissions:", rejected_submission_count, "\n")
cat("Number of unique complaints that only have rejected submissions:", rejections_only_count, "\n")
cat("Percentage of unique complaints that only have rejected submissions:", percentage_rejection_only, "\n")

# Create results data frame
results <- data.frame(
  Description = c(
    "Number of submissions",
    "Number of unique complaints",
    "Number of rejected submissions",
    "Average number of rejections per unique case number",
    "Max number of rejected submissions for one case number",
    "Number of unique complaints that only have rejected submissions",
    "Percentage of unique complaints that only have rejected submissions",
    "Average number of rejections per case number for complaints that only have rejected submissions"
  ),
  Value = c(
    all_submission_count,
    unique_submission_count,
    rejected_submission_count,
    average_rejections$avg_rejections,
    max_rejections$max_rejections,
    rejections_only_count,
    percentage_rejection_only,
    rej_only_average_rejections$rej_only_avg
  ),
  stringsAsFactors = FALSE
)

write.csv(
  results, 
  paste0("../results/analysis/", selected_state, "_GeneralReport.csv"),
  row.names = FALSE,
  quote = TRUE
)





# PRIMARY REMEDY CODE


# Read the data (replace 'path_to_your_csv' with the actual file path)
primaryreasonbreakdown <- uniquesubmissions

# Ensure relevant columns are numeric
primaryreasonbreakdown <- primaryreasonbreakdown %>%
  mutate(
    subcount = as.numeric(`Total.number.of.submissions.associated.with.this.CASENBR`),
    rejcount = as.numeric(`Total.number.of.rejections.associated.with.this.CASENBR`),
    cldclocount = as.numeric(`Total.number.of.Closed.Denied.or.Closed.Other.status.updates.associated.with.this.CASENBR`),
    clgacccount = as.numeric(`Total.number.of.Closed.Granted.or.Closed.Accepted.status.updates.associated.with.this.CASENBR`),
    only_rejected = ifelse(subcount == rejcount, 1, 0) # Add column for only_rejected
  )

# Filter rows for Closed Granted/Accepted Counts
CLGACC <- primaryreasonbreakdown %>%
  filter(clgacccount > 0)

# Create a breakdown for Closed Granted/Accepted Counts
clgacc_breakdown <- CLGACC %>%
  count(`Primary.Remedy.Subject`, name = "Closed Granted/Accepted Count")

# Filter rows for Closed Denied/Closed Other Counts
CLDCLO <- primaryreasonbreakdown %>%
  filter(
    cldclocount >= 1, # Must have 1 or more Closed Denied/Closed Other statuses
    clgacccount == 0  # Must have 0 Closed Granted/Accepted statuses
  )

# Create a breakdown for Closed Denied/Closed Other Counts
cldclo_breakdown <- CLDCLO %>%
  count(`Primary.Remedy.Subject`, name = "Closed Denied/Closed Other Count")

# Merge the breakdowns into the primary dataset
primaryreasonbreakdown <- primaryreasonbreakdown %>%
  left_join(clgacc_breakdown, by = "Primary.Remedy.Subject") %>%
  left_join(cldclo_breakdown, by = "Primary.Remedy.Subject") %>%
  mutate(
    `Closed Granted/Accepted Count` = coalesce(`Closed Granted/Accepted Count`, 0),
    `Closed Denied/Closed Other Count` = coalesce(`Closed Denied/Closed Other Count`, 0)
  )

# Analyze the data to get the top primary subjects with desired columns
analysis <- primaryreasonbreakdown %>%
  group_by(`Primary.Remedy.Subject`) %>%
  summarize(
    `Unique Complaint Count` = n(),
    `Percentage of All Unique Complaints` = round((`Unique Complaint Count` / nrow(primaryreasonbreakdown)) * 100, 2),
    `Closed Granted/Accepted Count` = first(`Closed Granted/Accepted Count`),
    `Closed Granted/Accepted Percentage` = round((`Closed Granted/Accepted Count` / `Unique Complaint Count`) * 100, 2),
    `Closed Denied/Closed Other Count` = first(`Closed Denied/Closed Other Count`),
    `Percentage Closed Denied/Closed Other` = round((`Closed Denied/Closed Other Count` / `Unique Complaint Count`) * 100, 2),
    `Rejected Only Count` = sum(only_rejected, na.rm = TRUE),
    `Percentage Rejected Only` = round((`Rejected Only Count` / `Unique Complaint Count`) * 100, 2)
  ) %>%
  arrange(desc(`Unique Complaint Count`)) # Sort by total complaints in descending order

# Save the result to a CSV file
write.csv(analysis, paste0("../results/analysis/", selected_state, "_PrimarySubjectAnalysis.csv"), row.names = FALSE, quote = TRUE)








# SECONDARY REMEDY CODE

# Read the data (reuse the original dataset to avoid confusion)
secondaryreasonbreakdown <- uniquesubmissions

# Ensure relevant columns are numeric
secondaryreasonbreakdown <- secondaryreasonbreakdown %>%
  mutate(
    subcount = as.numeric(`Total.number.of.submissions.associated.with.this.CASENBR`),
    rejcount = as.numeric(`Total.number.of.rejections.associated.with.this.CASENBR`),
    cldclocount = as.numeric(`Total.number.of.Closed.Denied.or.Closed.Other.status.updates.associated.with.this.CASENBR`),
    clgacccount = as.numeric(`Total.number.of.Closed.Granted.or.Closed.Accepted.status.updates.associated.with.this.CASENBR`),
    only_rejected = ifelse(subcount == rejcount, 1, 0) # Add column for only_rejected
  )

# Filter rows for Closed Granted/Accepted Counts
CLGACC_secondary <- secondaryreasonbreakdown %>%
  filter(clgacccount > 0)

# Create a breakdown for Closed Granted/Accepted Counts
clgacc_breakdown_secondary <- CLGACC_secondary %>%
  count(`Remedy.Subject.Code.Translation`, name = "Closed Granted/Accepted Count")

# Filter rows for Closed Denied/Closed Other Counts
CLDCLO_secondary <- secondaryreasonbreakdown %>%
  filter(
    cldclocount >= 1, # Must have 1 or more Closed Denied/Closed Other statuses
    clgacccount == 0  # Must have 0 Closed Granted/Accepted statuses
  )

# Create a breakdown for Closed Denied/Closed Other Counts
cldclo_breakdown_secondary <- CLDCLO_secondary %>%
  count(`Remedy.Subject.Code.Translation`, name = "Closed Denied/Closed Other Count")

# Merge the breakdowns into the secondary dataset
secondaryreasonbreakdown <- secondaryreasonbreakdown %>%
  left_join(clgacc_breakdown_secondary, by = "Remedy.Subject.Code.Translation") %>%
  left_join(cldclo_breakdown_secondary, by = "Remedy.Subject.Code.Translation") %>%
  mutate(
    `Closed Granted/Accepted Count` = coalesce(`Closed Granted/Accepted Count`, 0),
    `Closed Denied/Closed Other Count` = coalesce(`Closed Denied/Closed Other Count`, 0)
  )

# Analyze the data to get the top secondary subjects with desired columns
analysis_secondary <- secondaryreasonbreakdown %>%
  group_by(`Remedy.Subject.Code.Translation`) %>%
  summarize(
    `Unique Complaint Count` = n(),
    `Percentage of All Unique Complaints` = round((`Unique Complaint Count` / nrow(secondaryreasonbreakdown)) * 100, 2),
    `Closed Granted/Accepted Count` = first(`Closed Granted/Accepted Count`),
    `Closed Granted/Accepted Percentage` = round((`Closed Granted/Accepted Count` / `Unique Complaint Count`) * 100, 2),
    `Closed Denied/Closed Other Count` = first(`Closed Denied/Closed Other Count`),
    `Percentage Closed Denied/Closed Other` = round((`Closed Denied/Closed Other Count` / `Unique Complaint Count`) * 100, 2),
    `Rejected Only Count` = sum(only_rejected, na.rm = TRUE),
    `Percentage Rejected Only` = round((`Rejected Only Count` / `Unique Complaint Count`) * 100, 2)
  ) %>%
  arrange(desc(`Unique Complaint Count`)) # Sort by total complaints in descending order

# Save the result to a CSV file
write.csv(analysis_secondary, paste0("../results/analysis/", selected_state, "_SecondarySubjectAnalysis.csv"), row.names = FALSE, quote = TRUE)







library(ggplot2)

ggplot(analysis, aes(x = reorder(`Primary.Remedy.Subject`, -`Unique Complaint Count`), 
                     y = `Unique Complaint Count`)) +
  geom_bar(stat = "identity", fill = "steelblue") +
  coord_flip() +
  labs(
    title = "NY Unique Complaint Count by Primary Remedy Subject",
    x = "Primary Remedy Subject",
    y = "Unique Complaint Count"
  ) +
  theme_minimal()

# Save with wider dimensions
ggsave(
  filename = paste0("../results/analysis/", selected_state, "_UniqueComplaintBreakdown1.png"),
  width = 16, 
  height = 6,
  units = "in"
)
  






# Reshape the data
analysis_long <- analysis %>%
  pivot_longer(
    cols = c(`Closed Granted/Accepted Count`, `Closed Denied/Closed Other Count`, `Rejected Only Count`),
    names_to = "Status",
    values_to = "Count"
  )

# Create the plot
complaint_plot <- ggplot(analysis_long, aes(x = reorder(`Primary.Remedy.Subject`, -`Unique Complaint Count`), 
                                            y = Count, fill = Status)) +
  geom_bar(stat = "identity") +
  coord_flip() +
  labs(
    title = "NY Unique Complaint Breakdown by Status",
    x = "Primary Remedy Subject",
    y = "Count",
    fill = "Status"
  ) +
  theme_minimal()

# Save with wider dimensions
ggsave(
  filename = paste0("../results/analysis/", selected_state, "_UniqueComplaintBreakdown2.png"),
  width = 16, 
  height = 6,
  units = "in"
)
  








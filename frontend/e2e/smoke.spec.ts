import { expect, test, type Page } from "@playwright/test";

const clip = (name: string) => ({
  name,
  mimeType: "video/mp4",
  buffer: Buffer.from("sample clip; the mocked API does not read it"),
});

async function choose(page: Page, name: string) {
  await page.getByLabel("Video file").setInputFiles(clip(name));
}

test("a job goes from new to reviewed", async ({ page }) => {
  await page.goto("/");
  await page.getByRole("button", { name: "Start job" }).click();
  await expect(page.getByTestId("token")).toHaveText(/^[A-HJ-NP-Z2-9]{4}$/);

  await choose(page, "symptom.mp4");
  await page.getByLabel("Audio file").setInputFiles(clip("voice.m4a"));
  await page.getByLabel("Or type what is wrong").fill("water comes out slowly");
  await page.getByRole("button", { name: "Find likely causes" }).click();

  await expect(page.getByRole("heading", { name: "2. Run this check" })).toBeVisible();
  await expect(page.getByText("पानी धीरे आ रहा है")).toBeVisible();
  await choose(page, "check.mp4");
  await page.getByRole("button", { name: "Upload check" }).click();

  await page.getByRole("button", { name: "Confirm this cause" }).first().click();
  await expect(page.getByRole("heading", { name: "4. Repair" })).toBeVisible();
  for (const box of await page.getByLabel("I approve this step").all()) await box.check();
  await choose(page, "closeup.mp4");
  await page.getByRole("button", { name: "Upload close-up" }).click();

  await expect(page.getByRole("heading", { name: "5. Functional test" })).toBeVisible();
  await choose(page, "test.mp4");
  await page.getByLabel("Time to fill to the line (s)").fill("20");
  await page.getByLabel("Hose height (cm)").fill("20");
  await page.getByLabel("Water level (cm)").fill("8");
  await page.getByRole("button", { name: "Upload and verify" }).click();

  await expect(
    page.getByRole("heading", { name: "Passed these checks under these conditions" }),
  ).toBeVisible();
  await expect(page.getByText("Not enough evidence")).toHaveCount(0);

  await page.getByRole("link", { name: "Service record" }).click();
  await expect(page.getByRole("heading", { name: "Service record" })).toBeVisible();
  await page.goBack();

  await page.getByRole("link", { name: "Model calls and cost" }).click();
  await expect(page.getByRole("heading", { name: "triage" })).toBeVisible();
  await page.getByRole("link", { name: "Back to the job" }).click();

  await page.getByRole("link", { name: "Manager review" }).click();
  await page.getByRole("button", { name: "Approve record" }).click();
  await expect(page.getByText("Manager approved this record.")).toBeVisible();
});

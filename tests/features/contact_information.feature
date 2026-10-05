Feature: Contact information follows FedRAMP advisor schema 2.0.0
  As a SunStone Secure maintainer
  I want contactInformation published as the shared contact object
  So that the generated JSON validates against the current schema

  Scenario: README metadata uses the contact object
    Given the README defines contactInformation with name, title, email, phone and website
    When the advisor information JSON is built
    Then contactInformation is a JSON object with those five fields

  Scenario: Legacy string-array contact metadata is rejected
    Given the README defines contactInformation as an array of strings
    When the advisor information JSON is built
    Then the build fails with a message that contactInformation must be an object

  Scenario Outline: Invalid contact values are rejected
    Given the README contactInformation has <problem>
    When the advisor information JSON is built
    Then the build fails

    Examples:
      | problem                |
      | a missing jobTitle     |
      | an invalid email       |
      | a non-absolute website |
      | an unexpected field    |

enum Category {
    @@dynamic
}
function PickBestCategory(text: string) -> Category {
    client "openai/gpt-4o-mini"
    prompt #"
        Witch category best describes the following text?
        {{ctx.output_format}}
        {{_.role('user')}}
        {{text}}
    "#
}

test TestName {
  functions [PickBestCategory]
  type_builder{
    dynamic enum Category {
        Category1 @description(#"
            for placeholder text
        "#)
        Category2 @description(#"
            for debug logs
        "#)
        Category3 @description(#"
            for error logs
        "#)
    }
  }
  args {
    text #"
      hello world
    "#
  }
}
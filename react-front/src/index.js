import React from 'react';
import ReactDOM from 'react-dom';
import './index.css';
import * as serviceWorker from './serviceWorker';
import "antd/dist/antd.css";
import { Input, Button, Tag } from "antd";
import axios from 'axios';
import ContentEditable from 'react-contenteditable';
import label_colors from "./colors.js"

class MainPage extends React.Component{
  constructor(props){
    super(props);
    this.state = {
      text_data : "",
      output_data: "",
      html : "",
      emptyText: true
    }
  }

  handleTextAreaChange = (e) => {
    this.setState({ text_data: e.target.value,
                    emptyText: e.target.value === "" ? true : false})
  }

  parseButtonClick = (e) => {
    var data = null
    axios.post('http://localhost:5000/api/tag', {
      data: this.state.text_data
    })
    .then((response) => {
      console.log(response);
      if (response.status === 200){
        this.setState({output_data : response.data});
        this.highlightOutput(response.data);
        console.log(this.state)
      }

    })
    .catch((error) => {
      this.setState({output_data : error});
    });
  }

  highlightSentence = (sentence, tokens, color) => {
    for (var j in sentence){
      for (var range_ind in sentence[j].ranges){
        var token_ind = sentence[j].ranges[range_ind];
        tokens[token_ind] = "<span style=\"background-color:" + color + "\">"+ tokens[token_ind] + "</span>";
      }
    }
  }

  highlightOutput = (outputData) => {
    //Foratting output by color
    var output = []
    for (var i = 0; i < outputData.data.length; i++){
      var sentence = outputData.data[i]
      var tokens = [... sentence.tokens]
      if (sentence.valid){
        //coloring tagging
        this.highlightSentence(sentence.ingredients, tokens, label_colors.ingredients)
        this.highlightSentence(sentence.units, tokens, label_colors.units)
        this.highlightSentence(sentence.amounts, tokens, label_colors.amounts)
        output.push(tokens.join(" "));
      }
    }
    this.setState({html: output.join("<br>")});
  }

  download = (e) => {
    var fileDownload = require('js-file-download');
    fileDownload(JSON.stringify(this.state.output_data), 'tagged_ingredients.json');
  }

  clear = () => {
    this.setState({ text_data: "",
                    html: "",
                    emptyText: true});
  }

  render(){
    const placeholderTxt = "Enter a list of recipie ingredients: i.e.\n\
1 1/2 tablespoons sugar\n\
2 cups milk\n\
..."

    const style = {
      text_area : {
        paddingLeft:10,
        paddingRight:10,
        paddingTop:3,
        height: 350,
        width: 500,
        resize: "none",
        borderStyle:"solid",
        borderColor:"lightgrey",
        borderRadius: 3,
        borderWidth:1,
        backgroundColor:"white"
      },
      header : {
        color:"white",
        margin:"auto",
        fontSize:"24px"
      }
    };

    return(
      <div style={{backgroundColor:label_colors.backgroundGrey, padding:10}}>

      <div style={style.header}>
        Ingredients Parser
      </div>

        {
        // Top row
        }

        <div style={{
          display:"flex",
          flexDirection:"row",
          alignItems: "center",
          justifyContent: "center",
        }}>

          <div style={{margin:10, height: 370, width: 520}}>

            <Input.TextArea
            style = {{height: 350, width: 500, resize: "none"}}
            autoSize = {true}
            placeholder = {placeholderTxt}
            value = {this.state.text_data}
            onChange = {this.handleTextAreaChange}/>

            <div style = {{marginTop: 10}}>
              <Button
              type="primary"
              style={{marginRight: 5}}
              disabled={this.state.emptyText}
              onClick={this.parseButtonClick}>
                Parse Ingredients
              </Button>

              <Button
              onClick={this.clear}
              disabled={this.state.emptyText}>
                Clear
              </Button>
            </div>
          </div>

          <div style={{margin:10, height: 370, width: 520}}>
            <ContentEditable
            style={style.text_area}
            innerRef={this.contentEditable}
            html={this.state.html} // innerHTML of the editable div
            disabled={true}       // use true to disable editing
            />
            <div style={{marginTop: 10}}>
              <Tag
              style={{color: label_colors.backgroundGrey}}
              color={label_colors.ingredients}>
                Ingredients
              </Tag>
              <Tag
              style={{color: label_colors.backgroundGrey}}
              color={label_colors.amounts}>
                Amounts
              </Tag>
              <Tag
              style={{color: label_colors.backgroundGrey}}
              color={label_colors.units}>
                Units
              </Tag>
            </div>
          </div>

      </div>

      {
      // Bottom row
      }

      <div style={{margin:"auto", marginTop:20, width:"50%"}}>
        <Input.TextArea
        style = {{height: 350, width: 900, resize: "none"}}
        value = {JSON.stringify(this.state.output_data, null, 2)}
        />
        <div style = {{marginTop: 10}}>
          <Button icon="download"
          onClick={this.download}
          type="primary"
          disabled={this.state.output_data === "" ? true : false}>
            Download Json
          </Button>
        </div>
      </div>
      </div>
    );
  }
}


ReactDOM.render(<MainPage />, document.getElementById('root'));

// If you want your app to work offline and load faster, you can change
// unregister() to register() below. Note this comes with some pitfalls.
// Learn more about service workers: https://bit.ly/CRA-PWA
serviceWorker.unregister();

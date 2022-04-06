function mouseover(id)
{
    let m_over = document.getElementById(""+id+"m-o");
    setvisible(m_over);
}
function mouseout(id)
{
    let m_over = document.getElementById(""+id+"m-o");
    sethidden(m_over);
}
function setvisible(element) 
{
    element.style.animationName = 'show';
    element.style.visibility = 'visible';
    element.style.animationPlayState = 'running';
}
function sethidden(element) 
{
    element.style.animationName = 'hide';
    element.style.animationPlayState = 'running';
    element.addEventListener('animationend', () =>  {
        element.style.visibility = 'hidden';
      });
}
function onclick(id, product)
{
    if (id == "less")
    {
        int(produto) = document.querySelector("#"+product).value;
        document.querySelector("#"+product).innerHTML = produto++;
    }
}
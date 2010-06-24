<xsl:stylesheet version='1.0'
 xmlns:xsl='http://www.w3.org/1999/XSL/Transform'
 xmlns:bw='python://botoweb/xslt_functions'
 xmlns:fn='http://www.w3.org/2005/xpath-functions'
 xmlns:boto='http://code.google.com/p/boto-web/wiki/FilterSchema'>
	<xsl:include href="base.xsl"/>
	<!-- Pull all the authorization out of the DB, just like with the index -->
	<xsl:template match="node()[@id]" priority="5">
		<xsl:if test="bw:hasAuth('GET', name())">
			<xsl:copy>
				<xsl:apply-templates select="@*"/>
				<xsl:apply-templates select="*" mode="object"/>
			</xsl:copy>
		</xsl:if>
	</xsl:template>

	<xsl:template match="node()" mode="object">
		<xsl:if test="bw:hasAuth('GET', .., name())">
			<xsl:apply-templates select="." mode="copy"/>
		</xsl:if>
	</xsl:template>

	<xsl:template match="@*|node()" mode="copy">
		<xsl:copy>
			<xsl:apply-templates select="@*|node()" mode="copy"/>
		</xsl:copy>
	</xsl:template>
</xsl:stylesheet>
